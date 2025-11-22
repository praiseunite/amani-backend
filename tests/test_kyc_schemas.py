"""
Tests for KYC schemas validation.
"""

import pytest
from pydantic import ValidationError

from app.schemas.kyc import KycCreate, KycUpdate, KycApproval
from app.models.kyc import KycType, KycStatus


class TestKycSchemas:
    """Test KYC schema validation."""

    def test_kyc_create_valid_kyc(self):
        """Test valid KYC creation data."""
        data = {"type": KycType.KYC, "nin_or_passport": "ABC123456", "security_code": "1234"}

        kyc = KycCreate(**data)

        assert kyc.type == KycType.KYC
        assert kyc.nin_or_passport == "ABC123456"
        assert kyc.security_code == "1234"

    def test_kyc_create_valid_kyb(self):
        """Test valid KYB creation data."""
        data = {"type": KycType.KYB, "nin_or_passport": "BN123456789", "security_code": "5678"}

        kyc = KycCreate(**data)

        assert kyc.type == KycType.KYB
        assert kyc.nin_or_passport == "BN123456789"

    def test_kyc_create_with_optional_fields(self):
        """Test KYC creation with optional fingerprint and image."""
        data = {
            "type": KycType.KYC,
            "nin_or_passport": "ABC123456",
            "security_code": "1234",
            "fingerprint": b"fingerprint_data",
            "image": b"image_data",
        }

        kyc = KycCreate(**data)

        assert kyc.fingerprint == b"fingerprint_data"
        assert kyc.image == b"image_data"

    def test_kyc_create_nin_too_short(self):
        """Test KYC creation with NIN/passport too short."""
        data = {
            "type": KycType.KYC,
            "nin_or_passport": "AB",  # Less than 5 characters
            "security_code": "1234",
        }

        with pytest.raises(ValidationError):
            KycCreate(**data)

    def test_kyc_create_security_code_too_short(self):
        """Test KYC creation with security code too short."""
        data = {
            "type": KycType.KYC,
            "nin_or_passport": "ABC123456",
            "security_code": "12",  # Less than 4 characters
        }

        with pytest.raises(ValidationError):
            KycCreate(**data)

    def test_kyc_create_missing_required_fields(self):
        """Test KYC creation with missing required fields."""
        data = {"type": KycType.KYC}

        with pytest.raises(ValidationError):
            KycCreate(**data)

    def test_kyc_update_partial(self):
        """Test partial KYC update."""
        data = {"status": KycStatus.APPROVED}

        update = KycUpdate(**data)

        assert update.status == KycStatus.APPROVED
        assert update.rejection_reason is None

    def test_kyc_approval_approved(self):
        """Test KYC approval."""
        data = {"status": KycStatus.APPROVED, "approval_code": "APPR123"}

        approval = KycApproval(**data)

        assert approval.status == KycStatus.APPROVED
        assert approval.approval_code == "APPR123"

    def test_kyc_approval_rejected(self):
        """Test KYC rejection."""
        data = {"status": KycStatus.REJECTED, "rejection_reason": "Invalid document"}

        approval = KycApproval(**data)

        assert approval.status == KycStatus.REJECTED
        assert approval.rejection_reason == "Invalid document"
