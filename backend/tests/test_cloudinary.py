import pytest

from app import create_app
from services import cloudinary_service


@pytest.fixture()
def app():
    app = create_app("testing")
    app.config.update(TESTING=True)
    return app


def test_cloudinary_service_has_expected_interface():
    assert callable(cloudinary_service.upload_video)
    assert callable(cloudinary_service.verify_video)
    assert callable(cloudinary_service.delete_video)


def test_cloudinary_folder_is_configured():
    assert isinstance(cloudinary_service.CLOUDINARY_FOLDER, str)
    assert cloudinary_service.CLOUDINARY_FOLDER.strip()


def test_upload_video_requires_file_object():
    with pytest.raises((ValueError, TypeError)):
        cloudinary_service.upload_video(
            file_object=None,
            public_id="test-recording",
            folder=cloudinary_service.CLOUDINARY_FOLDER,
        )


def test_verify_video_requires_public_id():
    with pytest.raises((ValueError, TypeError)):
        cloudinary_service.verify_video("")


def test_delete_video_requires_public_id():
    with pytest.raises((ValueError, TypeError)):
        cloudinary_service.delete_video("")


def test_upload_video_delegates_to_cloudinary(monkeypatch):
    expected = {
        "public_id": "test-recording",
        "resource_type": "video",
        "secure_url": "https://example.com/test-recording.mp4",
    }

    class FakeUploader:
        @staticmethod
        def upload(*args, **kwargs):
            return expected

    monkeypatch.setattr(
        cloudinary_service,
        "cloudinary",
        type(
            "FakeCloudinary",
            (),
            {"uploader": FakeUploader},
        ),
    )

    result = cloudinary_service.upload_video(
        file_object=b"fake-video",
        public_id="test-recording",
        folder=cloudinary_service.CLOUDINARY_FOLDER,
    )

    assert result == expected


def test_verify_video_delegates_to_cloudinary(monkeypatch):
    expected = {
        "public_id": "test-recording",
        "resource_type": "video",
        "secure_url": "https://example.com/test-recording.mp4",
    }

    class FakeResource:
        @staticmethod
        def get(*args, **kwargs):
            return expected

    monkeypatch.setattr(
        cloudinary_service,
        "cloudinary",
        type(
            "FakeCloudinary",
            (),
            {"api": FakeResource},
        ),
    )

    result = cloudinary_service.verify_video("test-recording")

    assert result == expected


def test_delete_video_delegates_to_cloudinary(monkeypatch):
    expected = {
        "result": "ok",
    }

    class FakeUploader:
        @staticmethod
        def destroy(*args, **kwargs):
            return expected

    monkeypatch.setattr(
        cloudinary_service,
        "cloudinary",
        type(
            "FakeCloudinary",
            (),
            {"uploader": FakeUploader},
        ),
    )

    result = cloudinary_service.delete_video("test-recording")

    assert result == expected
