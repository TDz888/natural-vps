#!/usr/bin/env python3
import os
os.environ['DEBUG'] = 'false'
from app import create_app
from app.database import db

app = create_app()

# Test database
print("✓ Testing database...")
user_count = db.fetchone("SELECT COUNT(*) as count FROM users")
print(f"✓ Users table accessible: {user_count}")

# Test blueprints are registered
print("\n✓ Checking registered blueprints:")
for name, blueprint in app.blueprints.items():
    print(f"  - {name}")

# Test routes
print("\n✓ Available routes:")
for rule in app.url_map.iter_rules():
    if not rule.rule.startswith('/static'):
        print(f"  {rule.rule} -> {rule.endpoint}")

print("\n✅ All systems ready!")
