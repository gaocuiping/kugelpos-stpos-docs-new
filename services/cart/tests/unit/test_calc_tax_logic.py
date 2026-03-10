# Copyright 2025 masa@kugel
#
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

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

from app.models.documents.cart_document import CartDocument
from app.models.repositories.tax_master_repository import TaxMasterRepository
from app.services.logics import calc_tax_logic
from kugel_common.enums import TaxType, RoundMethod

class TestCalcTaxLogic:
    """Test suite for calc_tax_logic module."""

    @pytest.fixture
    def tax_master_repo(self):
        """Create a mock tax master repository."""
        return MagicMock(spec=TaxMasterRepository)

    @pytest.mark.asyncio
    async def test_calc_tax_async_external(self, tax_master_repo):
        """Test external tax calculation."""
        # Setup cart
        cart = CartDocument()
        tax_entry = CartDocument.Tax()
        tax_entry.tax_code = "T01"
        tax_entry.target_amount = 1000.0
        cart.taxes = [tax_entry]

        # Setup mock tax master
        tax_master = MagicMock()
        tax_master.tax_name = "Consumption Tax"
        tax_master.tax_type = TaxType.External.value
        tax_master.rate = 10.0
        tax_master.round_method = RoundMethod.Floor.value
        tax_master.round_digit = 0
        tax_master_repo.get_tax_by_code = AsyncMock(return_value=tax_master)

        # Execute
        result = await calc_tax_logic.calc_tax_async(cart, tax_master_repo)

        # Verify
        assert result.taxes[0].tax_amount == 100.0
        assert result.taxes[0].tax_type == TaxType.External.value

    @pytest.mark.asyncio
    async def test_calc_tax_async_internal(self, tax_master_repo):
        """Test internal tax calculation."""
        # Setup cart
        cart = CartDocument()
        tax_entry = CartDocument.Tax()
        tax_entry.tax_code = "T02"
        tax_entry.target_amount = 1100.0 # Includes 10% tax
        cart.taxes = [tax_entry]

        # Setup mock tax master
        tax_master = MagicMock()
        tax_master.tax_name = "Internal Tax"
        tax_master.tax_type = TaxType.Internal.value
        tax_master.rate = 10.0
        tax_master.round_method = RoundMethod.Floor.value
        tax_master.round_digit = 0
        tax_master_repo.get_tax_by_code = AsyncMock(return_value=tax_master)

        # Execute
        result = await calc_tax_logic.calc_tax_async(cart, tax_master_repo)

        # Verify: 1100 / 1.1 * 0.1 = 100
        assert result.taxes[0].tax_amount == 100.0
        assert result.taxes[0].tax_type == TaxType.Internal.value

    @pytest.mark.asyncio
    async def test_calc_tax_rounding_ceil(self, tax_master_repo):
        """test_calc_tax_rounding_ceil
        Test ceiling rounding method for tax calculation.
        """
        # Setup cart
        cart = CartDocument()
        tax_entry = CartDocument.Tax()
        tax_entry.tax_code = "T03"
        tax_entry.target_amount = 105.0
        cart.taxes = [tax_entry]

        # Setup mock tax master: 105 * 0.08 = 8.4
        tax_master = MagicMock()
        tax_master.tax_name = "Ceil Tax"
        tax_master.tax_type = TaxType.External.value
        tax_master.rate = 8.0
        tax_master.round_method = RoundMethod.Ceil.value
        tax_master.round_digit = 0
        tax_master_repo.get_tax_by_code = AsyncMock(return_value=tax_master)

        # Execute
        result = await calc_tax_logic.calc_tax_async(cart, tax_master_repo)

        # Verify: 8.4 rounded up to 0 decimal places is 9.0
        assert result.taxes[0].tax_amount == 9.0

    @pytest.mark.asyncio
    async def test_calc_tax_rounding_floor(self, tax_master_repo):
        """Test floor rounding method for tax calculation."""
        # Setup cart
        cart = CartDocument()
        tax_entry = CartDocument.Tax()
        tax_entry.tax_code = "T04"
        tax_entry.target_amount = 105.0
        cart.taxes = [tax_entry]

        # Setup mock tax master: 105 * 0.08 = 8.4
        tax_master = MagicMock()
        tax_master.tax_name = "Floor Tax"
        tax_master.tax_type = TaxType.External.value
        tax_master.rate = 8.0
        tax_master.round_method = RoundMethod.Floor.value
        tax_master.round_digit = 0
        tax_master_repo.get_tax_by_code = AsyncMock(return_value=tax_master)

        # Execute
        result = await calc_tax_logic.calc_tax_async(cart, tax_master_repo)

        # Verify: 8.4 rounded down to 0 decimal places is 8.0
        assert result.taxes[0].tax_amount == 8.0
