"""
SEO and metadata routes for visitor management system.
"""
from flask import Blueprint, current_app, send_from_directory
import os

seo_bp = Blueprint('seo', __name__)


@seo_bp.route('/robots.txt')
def robots():
    """Serve robots.txt file."""
    return send_from_directory(current_app.static_folder, 'robots.txt')


@seo_bp.route('/sitemap.xml')
def sitemap():
    """Serve sitemap.xml file."""
    return send_from_directory(current_app.static_folder, 'sitemap.xml')


@seo_bp.route('/favicon.ico')
def favicon():
    """Serve favicon if it exists."""
    favicon_path = os.path.join(current_app.static_folder, 'favicon.ico')
    if os.path.exists(favicon_path):
        return send_from_directory(current_app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')
    return '', 204  # No content if favicon doesn't exist
