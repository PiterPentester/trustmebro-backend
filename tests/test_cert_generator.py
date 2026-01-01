import pytest
from unittest.mock import Mock, patch, MagicMock
from reportlab.lib.pagesizes import A4
from core.cert_generator import TrustMeBroCertificate


class TestTrustMeBroCertificate:
    @pytest.fixture
    def cert_generator(self):
        with patch("core.cert_generator.redis.Redis"):
            return TrustMeBroCertificate("redis://localhost", "http://localhost:8080")

    @patch("core.cert_generator.BaseDocTemplate")
    @patch("core.cert_generator.Image")
    @patch("core.cert_generator.redis.Redis")
    def test_create_certificate(
        self, mock_redis_cls, mock_image_cls, mock_doc_template, cert_generator
    ):
        # Mock Redis instance
        mock_redis_instance = Mock()
        mock_redis_cls.return_value = mock_redis_instance

        # Mock DocTemplate
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc

        # Mock Image
        mock_image_instance = MagicMock()
        mock_image_cls.return_value = mock_image_instance

        # Test data
        cert_type = "achievement"
        recipient = "Test User"
        item_to_prove = "Test Item"

        # Mock os.listdir and random.choice for image selection
        with (
            patch("os.listdir", return_value=["logo.png"]),
            patch("random.choice", return_value="logo.png"),
            patch("os.path.join", return_value="assets/badges/logo.png"),
        ):
            validation_number = cert_generator.create_certificate(
                cert_type, recipient, item_to_prove
            )

        assert validation_number is not None
        assert len(validation_number) > 0

        # Verify Redis storage
        mock_redis_instance.set.assert_called_once()

        # Verify PDF generation
        mock_doc_template.assert_called_once()
        mock_doc.build.assert_called_once()

    @patch("core.cert_generator.BaseDocTemplate")
    @patch("core.cert_generator.Image")
    @patch("core.cert_generator.redis.Redis")
    def test_create_certificate_portrait(
        self, mock_redis_cls, mock_image_cls, mock_doc_template, cert_generator
    ):
        mock_redis_cls.return_value = Mock()
        mock_doc_template.return_value = MagicMock()
        mock_image_cls.return_value = MagicMock()

        with (
            patch("os.listdir", return_value=["logo.png"]),
            patch("random.choice", return_value="logo.png"),
            patch("os.path.join", return_value="assets/badges/logo.png"),
        ):
            cert_generator.create_certificate(
                "achievement", "User", "Item", orientation="portrait"
            )

        # Check that pagesize corresponds to A4 (Portrait)
        # A4 is (595.27, 841.89)
        call_args = mock_doc_template.call_args
        assert call_args is not None
        _, kwargs = call_args
        assert kwargs["pagesize"] == A4

    @patch("core.cert_generator.BaseDocTemplate")
    @patch("core.cert_generator.Image")
    @patch("core.cert_generator.redis.Redis")
    def test_create_certificate_landscape(
        self, mock_redis_cls, mock_image_cls, mock_doc_template, cert_generator
    ):
        mock_redis_cls.return_value = Mock()
        mock_doc_template.return_value = MagicMock()
        mock_image_cls.return_value = MagicMock()

        with (
            patch("os.listdir", return_value=["logo.png"]),
            patch("random.choice", return_value="logo.png"),
            patch("os.path.join", return_value="assets/badges/logo.png"),
        ):
            cert_generator.create_certificate(
                "achievement", "User", "Item", orientation="landscape"
            )

        # Check that pagesize corresponds to Landscape A4
        # Landscape A4 is (841.89, 595.27) aka (A4[1], A4[0])
        call_args = mock_doc_template.call_args
        assert call_args is not None
        _, kwargs = call_args
        assert kwargs["pagesize"] == (A4[1], A4[0])

    def test_generate_validation_number(self, cert_generator):
        number = cert_generator.generate_validation_number("User", "Item")
        assert isinstance(number, str)
        assert len(number) == 64  # SHA256 hex digest is 64 chars
