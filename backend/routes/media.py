import os
from flask import Blueprint, Response, current_app as app, send_from_directory, jsonify, abort, url_for, request
from models.epub_metadata import EpubMetadata
from functions.db import get_session
from config.config import config
from config.logger import logger

media_bp = Blueprint('media', __name__)

@media_bp.route('/api/covers/<string:book_identifier>', methods=['GET'])
def get_cover(book_identifier):
    """
    Serve cover images with browser-side caching enabled to reduce repeated requests.
    """
    session = get_session()
    book_record = session.query(EpubMetadata).filter_by(identifier=str(book_identifier)).first()

    if not book_record or not book_record.cover_image_data:
        placeholder_path = os.path.join(app.static_folder, 'placeholder.jpg')
        with open(placeholder_path, 'rb') as f:
            placeholder_image = f.read()
        # Set browser caching headers
        return Response(placeholder_image, mimetype='image/jpeg', headers={
            "Cache-Control": "public, max-age=259200"  # Cache for 1 year
        })

    # Set browser caching headers for actual cover
    logger.debug(f"Content media type is {book_record.cover_media_type}")
    return Response(book_record.cover_image_data, mimetype=book_record.cover_media_type, headers={
        "Cache-Control": "public, max-age=259200"  # Cache for 1 year
    })

@media_bp.route('/download/<string:book_identifier>', methods=['GET'])
def download(book_identifier):
    session = get_session()

    # Optionally validate that the relative_path exists in the database
    book_record = session.query(EpubMetadata).filter_by(identifier=str(book_identifier)).first()
    logger.debug(f"BASE DIR: {config.BASE_DIRECTORY}")

    if not book_record:
        abort(404, description="Resource not found")

    relative_path = book_record.relative_path
    # Ensure the base directory remains consistent
    try:
        custom_file_header = request.headers.get("file")
        if config.ENVIRONMENT == "test" and custom_file_header == "not_found":
            raise FileNotFoundError
        return send_from_directory(config.BASE_DIRECTORY, relative_path, as_attachment=True)
    except FileNotFoundError:
        abort(404, description="File not found")

@media_bp.route('/stream/<string:book_identifier>', methods=['GET'])
def stream(book_identifier):
    session = get_session()

    # Fetch the book's metadata from the database
    book_record = session.query(EpubMetadata).filter_by(identifier=book_identifier).first()
    if not book_record:
        abort(404, description="Book not found.")

    # Get the relative path of the book
    relative_path = book_record.relative_path

    # Combine base directory + relative path to get the full file path
    full_path = os.path.join(config.BASE_DIRECTORY, relative_path)

    # Check if the file exists
    if not os.path.exists(full_path):
        abort(404, description="ePub file not found.")

    # Generate the correct accessible URL for this file
    epub_file_url = config.BASE_URL.rstrip("/") + url_for('media.serve_book_file', filename=relative_path)

    return jsonify({"url": epub_file_url})

@media_bp.route('/files/<path:filename>', methods=['GET'])
def serve_book_file(filename):
    try:
        base_directory = config.BASE_DIRECTORY  # Root location of your ePub files
        custom_file_header = request.headers.get("file")
        if config.ENVIRONMENT == "test" and custom_file_header == "not_found":
            raise FileNotFoundError
        return send_from_directory(base_directory, filename)
    except FileNotFoundError:
        abort(404, description="File not found.")