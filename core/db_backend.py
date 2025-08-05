"""
SQLite database optimizations using Django signals
"""
from django.db import connection
from django.db.backends.signals import connection_created
from django.dispatch import receiver


@receiver(connection_created)
def set_sqlite_pragma(connection, **kwargs):
    """Set SQLite optimizations when connection is created"""
    if connection.vendor == 'sqlite':
        with connection.cursor() as cursor:
            # WAL mode for better performance and concurrency
            cursor.execute("PRAGMA journal_mode=WAL;")
            # Normal synchronization for better performance
            cursor.execute("PRAGMA synchronous=NORMAL;")
            # Increase cache size to 64MB
            cursor.execute("PRAGMA cache_size=-64000;")
            # Store temp data in memory
            cursor.execute("PRAGMA temp_store=MEMORY;")
            
        print("✅ SQLite optimizations applied (WAL mode, cache, etc.)")
