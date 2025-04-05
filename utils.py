from functools import wraps
from flask import abort
from flask_login import current_user
import json

def has_role(role_name):
    """Check if the current user has a specific role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            for role in current_user.roles:
                if role.name == role_name:
                    return f(*args, **kwargs)
            
            abort(403)
        return decorated_function
    return decorator

def has_permission(module, permission):
    """Check if the current user has a specific permission in a module."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            for role in current_user.roles:
                if role.module == module:
                    permissions = json.loads(role.permissions)
                    if permissions.get(permission, False):
                        return f(*args, **kwargs)
            
            abort(403)
        return decorated_function
    return decorator

def has_any_role(role_names):
    """Check if the current user has any of the specified roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            user_roles = {role.name for role in current_user.roles}
            if any(role in user_roles for role in role_names):
                return f(*args, **kwargs)
            
            abort(403)
        return decorated_function
    return decorator

def get_user_permissions(user, module=None):
    """Get all permissions for a user, optionally filtered by module."""
    permissions = {}
    
    for role in user.roles:
        if module and role.module != module:
            continue
        
        role_perms = json.loads(role.permissions)
        permissions.update(role_perms)
    
    return permissions

def user_can(user, module, permission):
    """Check if a user has a specific permission in a module."""
    for role in user.roles:
        if role.module == module:
            permissions = json.loads(role.permissions)
            if permissions.get(permission, False):
                return True
    return False
