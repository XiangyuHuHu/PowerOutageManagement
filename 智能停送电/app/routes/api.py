"""
兼容路由层（P1收敛）：
- 该文件仅保留历史入口，实际业务逻辑统一在 operations.py / approvals.py。
- 避免同一接口在多个文件重复实现导致行为不一致。
"""

from flask import Blueprint
from app.routes import operations, approvals

bp = Blueprint('api', __name__)


@bp.route('/api/power-apply', methods=['POST'])
def power_apply():
    return operations.power_apply()


@bp.route('/api/devices', methods=['GET'])
def get_devices():
    return operations.get_devices()


@bp.route('/api/my-devices', methods=['GET', 'PUT'])
def my_devices():
    return operations.my_devices()


@bp.route('/api/list', methods=['GET'])
def get_list():
    return operations.get_list()


@bp.route('/api/electrician-verify', methods=['POST'])
def electrician_verify():
    return operations.electrician_verify()


@bp.route('/api/repair-operation', methods=['POST'])
def repair_operation():
    return operations.repair_operation()


@bp.route('/api/power-on-apply', methods=['POST'])
def power_on_apply():
    return operations.power_on_apply()


@bp.route('/api/notifications', methods=['GET'])
def get_notifications():
    return operations.get_notifications()


@bp.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_notification_read(notification_id):
    return operations.mark_notification_read_route(notification_id)


@bp.route('/api/power-off-approve', methods=['POST'])
def power_off_approve():
    return approvals.power_off_approve()


@bp.route('/api/power-on-approve', methods=['POST'])
def power_on_approve():
    return approvals.power_on_approve()


@bp.route('/api/batch-approve-room', methods=['POST'])
def batch_approve_room():
    return approvals.batch_approve_room()


@bp.route('/api/application/<int:app_id>', methods=['GET'])
def get_application_detail(app_id):
    return approvals.get_application_detail(app_id)


@bp.route('/api/export/applications', methods=['GET'])
def export_applications():
    return approvals.export_applications()


@bp.route('/api/maintenance-batches', methods=['GET'])
def get_maintenance_batches():
    from app.routes import admin
    return admin.get_maintenance_batches()


@bp.route('/api/maintenance-batches', methods=['POST'])
def create_maintenance_batches():
    from app.routes import admin
    return admin.create_maintenance_batch()


@bp.route('/api/maintenance-batches/<int:batch_id>', methods=['GET'])
def get_maintenance_batch_detail(batch_id):
    from app.routes import admin
    return admin.get_maintenance_batch_detail(batch_id)


@bp.route('/api/maintenance-batches/<int:batch_id>/export', methods=['GET'])
def export_maintenance_batch(batch_id):
    from app.routes import admin
    return admin.export_maintenance_batch(batch_id)


@bp.route('/api/maintenance-batches/<int:batch_id>/approve', methods=['POST'])
def approve_maintenance_batch(batch_id):
    from app.routes import admin
    return admin.approve_maintenance_batch(batch_id)


@bp.route('/api/maintenance-batches/<int:batch_id>/close', methods=['POST'])
def close_maintenance_batch(batch_id):
    from app.routes import admin
    return admin.close_maintenance_batch(batch_id)
