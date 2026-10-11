ALLOWED_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}

MAX_FILE_SIZE = 5 * 1024 * 1024


def test_allowed_file_type():
    assert "application/pdf" in ALLOWED_TYPES


def test_jpeg_is_allowed():
    assert "image/jpeg" in ALLOWED_TYPES


def test_invalid_file_type():
    assert "text/plain" not in ALLOWED_TYPES


def test_file_size_limit():
    assert 5 * 1024 * 1024 == MAX_FILE_SIZE


def test_large_file_exceeds_limit():
    file_size = 6 * 1024 * 1024

    assert file_size > MAX_FILE_SIZE