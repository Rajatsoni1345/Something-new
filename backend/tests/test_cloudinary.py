from services import cloudinary_service


def test_cloudinary_folder_is_configured():
    assert isinstance(cloudinary_service.CLOUDINARY_FOLDER, str)
    assert cloudinary_service.CLOUDINARY_FOLDER.strip()


def test_upload_video_requires_file_object():
    try:
        cloudinary_service.upload_video(
            file_object=None,
            public_id="x",
            folder=cloudinary_service.CLOUDINARY_FOLDER,
        )
    except (ValueError, TypeError):
        return
    raise AssertionError("Expected ValueError or TypeError")


def test_upload_video_requires_public_id():
    try:
        cloudinary_service.upload_video(
            file_object=b"data",
            public_id="",
            folder=cloudinary_service.CLOUDINARY_FOLDER,
        )
    except (ValueError, TypeError):
        return
    raise AssertionError("Expected ValueError or TypeError")


def test_verify_video_requires_public_id():
    try:
        cloudinary_service.verify_video("")
    except (ValueError, TypeError):
        return
    raise AssertionError("Expected ValueError or TypeError")


def test_delete_video_requires_public_id():
    try:
        cloudinary_service.delete_video("")
    except (ValueError, TypeError):
        return
    raise AssertionError("Expected ValueError or TypeError")


def test_upload_video_delegates(monkeypatch):
    expected = {
        "public_id": "x",
        "resource_type": "video",
        "secure_url": "https://example.com/x.mp4",
    }

    class FakeUploader:
        @staticmethod
        def upload(*args, **kwargs):
            return expected

    class FakeCloud:
        uploader = FakeUploader()

    monkeypatch.setattr(
        cloudinary_service, "cloudinary", FakeCloud
    )
    monkeypatch.setattr(
        cloudinary_service, "_initialize_cloudinary", lambda: None
    )

    result = cloudinary_service.upload_video(
        file_object=b"data",
        public_id="x",
        folder=cloudinary_service.CLOUDINARY_FOLDER,
    )

    assert result == expected
