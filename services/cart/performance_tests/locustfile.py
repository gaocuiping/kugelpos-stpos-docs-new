# Copyright 2025 masa@kugel
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Locust performance test for Cart Service

This test simulates the following scenario (repeated continuously during test duration):
1. Create a cart
2. Add 20 items (with configurable second intervals, default: 3s)
3. Cancel the cart
4. Wait before repeating (configurable, default: 3s)

The test runs continuously for the specified duration, with each user
repeatedly executing the cart scenario. Errors are logged but do not
stop the test, ensuring continuous load generation.

Test can be run in two modes:
- Web UI mode: locust -f locustfile.py --host=http://localhost:8003
- Headless mode: locust -f locustfile.py --host=http://localhost:8003 --users 20 --spawn-rate 2 --run-time 30m --headless

Environment variables:
- PERF_TEST_ITEMS_PER_CART: Number of items per cart (default: 20)
- PERF_TEST_ITEM_ADD_INTERVAL: Seconds between item additions (default: 3)
- PERF_TEST_POST_CANCEL_WAIT: Seconds to wait after cart cancel (default: 3)
"""

from locust import HttpUser, task, between, events
import time
import logging
import random
from config import PerformanceTestConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CartPerformanceUser(HttpUser):
    """
    Simulates a user performing cart operations
    """

    # Wait time between tasks (0-1 seconds)
    wait_time = between(0, 1)

    def on_start(self):
        """
        Called when a simulated user starts executing tasks.
        Sets up authentication and configuration.
        """
        # Load configuration
        config = PerformanceTestConfig.from_env()

        self.api_key = config.api_key
        self.tenant_id = config.tenant_id
        self.terminal_id = f"{config.tenant_id}-5678-9"
        self.items_per_cart = config.items_per_cart
        self.item_add_interval = config.item_add_interval
        self.post_cancel_wait = config.post_cancel_wait

        self.headers = {"X-API-KEY": self.api_key}

        logger.info(f"User started with config: items={self.items_per_cart}, "
                   f"interval={self.item_add_interval}s, wait={self.post_cancel_wait}s")

    @task
    def cart_scenario(self):
        """
        Main test scenario:
        1. Create cart
        2. Add items (configurable count with configurable intervals)
        3. Cancel cart
        4. Wait before repeating

        Note: This task runs continuously during the test duration.
        Errors are logged but do not stop the user from continuing.
        """
        cart_id = None
        scenario_start_time = time.time()

        try:
            # Step 1: Create cart
            cart_id = self._create_cart()
            if not cart_id:
                logger.warning("Cart creation failed, waiting before retry...")
                time.sleep(5)  # Wait before retrying
                return

            # Step 2: Add items
            self._add_items(cart_id)

            # Step 3: Cancel cart
            self._cancel_cart(cart_id)

            # Step 4: Post-cancel wait
            time.sleep(self.post_cancel_wait)

            scenario_duration = time.time() - scenario_start_time
            logger.info(f"Scenario completed in {scenario_duration:.2f}s for cart {cart_id}")

        except Exception as e:
            logger.error(f"Scenario failed for cart {cart_id}: {str(e)}")
            # Don't raise - allow the task to continue for the next iteration
            time.sleep(5)  # Wait before next iteration after error

    def _create_cart(self) -> str:
        """
        Create a new cart

        Returns:
            cart_id if successful, None otherwise
        """
        create_req = {
            "transaction_type": 101,  # 101 = sales
            "user_id": f"perf_user_{int(time.time())}",
            "user_name": "Performance Test User"
        }

        with self.client.post(
            f"/api/v1/carts?terminal_id={self.terminal_id}",
            json=create_req,
            headers=self.headers,
            catch_response=True,
            name="POST /api/v1/carts (Create Cart)"
        ) as response:
            if response.status_code == 201:
                cart_id = response.json()["data"]["cartId"]
                response.success()
                logger.debug(f"Cart created: {cart_id}")
                return cart_id
            else:
                response.failure(f"Failed to create cart: {response.status_code} - {response.text}")
                logger.error(f"Cart creation failed: {response.status_code}")
                return None

    def _add_items(self, cart_id: str):
        """
        Add items to the cart with random unique items

        Args:
            cart_id: The cart ID to add items to

        Note: Continues adding items even if some fail, to maintain test continuity.
        """
        # Generate random unique item indices for this cart (avoid duplicates)
        # We have 100 items (ITEM000-ITEM099), so sample randomly without replacement
        item_indices = random.sample(range(100), self.items_per_cart)

        failed_items = 0

        for i, item_idx in enumerate(item_indices):
            item_data = [{
                "item_code": f"ITEM{item_idx:03d}",
                "quantity": 1,
                "unit_price": 100 + item_idx  # Varying price for diversity
            }]

            with self.client.post(
                f"/api/v1/carts/{cart_id}/lineItems?terminal_id={self.terminal_id}",
                json=item_data,
                headers=self.headers,
                catch_response=True,
                name="POST /api/v1/carts/[cart_id]/lineItems (Add Item)"
            ) as response:
                if response.status_code == 200:
                    response.success()
                    logger.debug(f"Item {i+1}/{self.items_per_cart} (ITEM{item_idx:03d}) added to cart {cart_id}")
                else:
                    response.failure(f"Failed to add item: {response.status_code} - {response.text}")
                    logger.warning(f"Item add failed for cart {cart_id}: {response.status_code}")
                    failed_items += 1
                    # Continue to next item instead of raising exception

            # Wait between item additions (except after the last item)
            if i < self.items_per_cart - 1:
                time.sleep(self.item_add_interval)

        if failed_items > 0:
            logger.warning(f"Cart {cart_id}: {failed_items}/{self.items_per_cart} items failed to add")

    def _cancel_cart(self, cart_id: str):
        """
        Cancel the cart

        Args:
            cart_id: The cart ID to cancel

        Note: Logs errors but does not raise exceptions to maintain test continuity.
        """
        with self.client.post(
            f"/api/v1/carts/{cart_id}/cancel?terminal_id={self.terminal_id}",
            headers=self.headers,
            catch_response=True,
            name="POST /api/v1/carts/[cart_id]/cancel (Cancel Cart)"
        ) as response:
            if response.status_code == 200:
                response.success()
                logger.debug(f"Cart cancelled: {cart_id}")
            else:
                response.failure(f"Failed to cancel cart: {response.status_code} - {response.text}")
                logger.warning(f"Cart cancel failed for {cart_id}: {response.status_code}")
                # Continue instead of raising exception


@events.test_start.add_listener
def on_test_start(environment, **_kwargs):
    """
    Called when the test starts
    """
    config = PerformanceTestConfig.from_env()
    logger.info("=" * 80)
    logger.info("Performance Test Starting")
    logger.info(f"Configuration:")
    logger.info(f"  - Items per cart: {config.items_per_cart}")
    logger.info(f"  - Item add interval: {config.item_add_interval}s")
    logger.info(f"  - Post-cancel wait: {config.post_cancel_wait}s")
    logger.info(f"  - Target host: {environment.host}")
    logger.info("=" * 80)


@events.test_stop.add_listener
def on_test_stop(environment, **_kwargs):
    """
    Called when the test stops
    """
    logger.info("=" * 80)
    logger.info("Performance Test Completed")
    logger.info("=" * 80)
