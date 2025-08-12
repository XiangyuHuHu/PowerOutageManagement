<template>
	<view class="repair-container">
		<view class="header">
			<view class="header-content">
				<view class="logo-icon">
					<text class="icon">🔧</text>
				</view>
				<view class="header-text">
					<text class="title">检修管理</text>
					<text class="subtitle">设备检修任务管理</text>
				</view>
			</view>
			<button class="back-btn" @click="goBack">
				<text class="back-icon">←</text>
				<text>返回</text>
			</button>
		</view>
		
		<view class="content">
			<!-- 统计卡片 -->
			<view class="stats-container">
				<view class="stat-card">
					<text class="stat-value">{{ stats.total }}</text>
					<text class="stat-label">总任务</text>
				</view>
				<view class="stat-card">
					<text class="stat-value">{{ stats.pending }}</text>
					<text class="stat-label">待处理</text>
				</view>
				<view class="stat-card">
					<text class="stat-value">{{ stats.inProgress }}</text>
					<text class="stat-label">进行中</text>
				</view>
				<view class="stat-card">
					<text class="stat-value">{{ stats.completed }}</text>
					<text class="stat-label">已完成</text>
				</view>
			</view>
			
			<!-- 任务列表 -->
			<view class="task-list">
				<view class="list-header">
					<text class="list-title">检修任务</text>
					<button class="add-btn" @click="showAddDialog">
						<text>+ 新建任务</text>
					</button>
				</view>
				
				<view v-if="loading" class="loading">
					<text>加载中...</text>
				</view>
				
				<view v-else-if="tasks.length === 0" class="empty">
					<text>暂无检修任务</text>
				</view>
				
				<view v-else class="task-items">
					<view 
						v-for="task in tasks" 
						:key="task.id" 
						class="task-item"
						@click="viewTask(task)"
					>
						<view class="task-info">
							<view class="task-header">
								<text class="task-title">{{ task.title }}</text>
								<view class="task-status" :class="'status-' + task.status">
									<text>{{ getStatusText(task.status) }}</text>
								</view>
							</view>
							<text class="task-description">{{ task.description }}</text>
							<view class="task-meta">
								<text class="task-device">设备: {{ task.deviceId }}</text>
								<text class="task-assignee">负责人: {{ task.assignee }}</text>
							</view>
							<view class="task-time">
								<text class="task-date">创建时间: {{ formatDateTime(task.created_at) }}</text>
								<text v-if="task.deadline" class="task-deadline">截止时间: {{ formatDateTime(task.deadline) }}</text>
							</view>
						</view>
						<view class="task-actions">
							<button class="action-btn edit-btn" @click.stop="editTask(task)">
								<text>编辑</text>
							</button>
							<button class="action-btn delete-btn" @click.stop="deleteTask(task.id)">
								<text>删除</text>
							</button>
						</view>
					</view>
				</view>
			</view>
		</view>
		
		<!-- 新建/编辑任务弹窗 -->
		<view v-if="showDialog" class="task-dialog" @click="closeDialog">
			<view class="dialog-content" @click.stop>
				<view class="dialog-header">
					<text class="dialog-title">{{ isEdit ? '编辑任务' : '新建任务' }}</text>
					<button class="close-btn" @click="closeDialog">
						<text>×</text>
					</button>
				</view>
				
				<view class="dialog-form">
					<view class="form-group">
						<text class="label">任务标题</text>
						<input class="input" v-model="taskForm.title" placeholder="请输入任务标题" />
					</view>
					
					<view class="form-group">
						<text class="label">任务描述</text>
						<textarea class="textarea" v-model="taskForm.description" placeholder="请输入任务描述" />
					</view>
					
					<view class="form-group">
						<text class="label">设备ID</text>
						<input class="input" v-model="taskForm.deviceId" placeholder="请输入设备ID" />
					</view>
					
					<view class="form-group">
						<text class="label">负责人</text>
						<input class="input" v-model="taskForm.assignee" placeholder="请输入负责人" />
					</view>
					
					<view class="form-group">
						<text class="label">任务状态</text>
						<picker 
							class="picker" 
							:value="statusIndex" 
							:range="statusOptions" 
							@change="onStatusChange"
						>
							<view class="picker-text">
								{{ statusOptions[statusIndex] }}
							</view>
						</picker>
					</view>
					
					<view class="form-group">
						<text class="label">截止时间</text>
						<picker 
							class="picker" 
							mode="date" 
							:value="taskForm.deadline" 
							@change="onDateChange"
						>
							<view class="picker-text">
								{{ taskForm.deadline || '请选择截止时间' }}
							</view>
						</picker>
					</view>
				</view>
				
				<view class="dialog-buttons">
					<button class="save-btn" @click="saveTask" :disabled="saving">
						<text>{{ saving ? '保存中...' : '保存' }}</text>
					</button>
					<button class="cancel-btn" @click="closeDialog">
						<text>取消</text>
					</button>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
export default {
	data() {
		return {
			tasks: [],
			stats: {
				total: 0,
				pending: 0,
				inProgress: 0,
				completed: 0
			},
			loading: false,
			showDialog: false,
			isEdit: false,
			taskForm: {
				id: null,
				title: '',
				description: '',
				deviceId: '',
				assignee: '',
				status: 'pending',
				deadline: ''
			},
			statusOptions: ['待处理', '进行中', '已完成', '已取消'],
			statusIndex: 0,
			saving: false
		}
	},
	
	onLoad() {
		this.fetchTasks();
	},
	
	methods: {
		getStatusText(status) {
			const statusMap = {
				'pending': '待处理',
				'in_progress': '进行中',
				'completed': '已完成',
				'cancelled': '已取消'
			};
			return statusMap[status] || status;
		},
		
		formatDateTime(timestamp) {
			if (!timestamp) return '';
			
			// 兼容iOS的日期格式处理
			let dateStr = timestamp;
			if (typeof timestamp === 'string') {
				// 将 "yyyy-MM-dd HH:mm:ss" 转换为 "yyyy/MM/dd HH:mm:ss" 以兼容iOS
				dateStr = timestamp.replace(/-/g, '/');
			}
			
			const date = new Date(dateStr);
			
			// 检查日期是否有效
			if (isNaN(date.getTime())) {
				return timestamp; // 如果解析失败，返回原始字符串
			}
			
			return date.toLocaleString('zh-CN', {
				year: 'numeric',
				month: '2-digit',
				day: '2-digit',
				hour: '2-digit',
				minute: '2-digit'
			});
		},
		
		async fetchTasks() {
			this.loading = true;
			try {
				// 获取真实的申请数据作为检修任务
				const response = await uni.request({
					url: 'http://localhost:5050/api/mp/applications',
					method: 'GET',
					header: {
						'Content-Type': 'application/json'
					},
					timeout: 15000
				});
				
				if (response.statusCode === 200) {
					// 将申请数据转换为检修任务格式
					this.tasks = response.data.map(app => ({
						id: app.id,
						title: `${app.deviceId} - ${app.reason}`,
						description: `申请人: ${app.applicant_name || app.applicant}, 原因: ${app.reason}`,
						deviceId: app.deviceId,
						assignee: app.applicant_name || app.applicant,
						status: this.mapApplicationStatusToTaskStatus(app.status),
						created_at: app.created_at,
						deadline: app.power_off_time,
						originalApplication: app // 保存原始申请数据
					}));
					
					this.updateStats();
					console.log('检修任务获取成功，共', this.tasks.length, '个任务');
				} else {
					console.error('获取检修任务失败，状态码:', response.statusCode);
					uni.showToast({
						title: '获取检修任务失败',
						icon: 'none'
					});
				}
			} catch (err) {
				console.error('获取检修任务失败:', err);
				uni.showToast({
					title: '网络错误',
					icon: 'none'
				});
			} finally {
				this.loading = false;
			}
		},
		
		mapApplicationStatusToTaskStatus(appStatus) {
			const statusMap = {
				'pending': 'pending',
				'approved': 'in_progress',
				'verified': 'in_progress',
				'repairing': 'in_progress',
				'repair_completed': 'completed',
				'completed': 'completed',
				'rejected': 'cancelled',
				'power_on_applied': 'completed',
				'power_on_rejected': 'cancelled'
			};
			return statusMap[appStatus] || 'pending';
		},
		
		updateStats() {
			this.stats.total = this.tasks.length;
			this.stats.pending = this.tasks.filter(t => t.status === 'pending').length;
			this.stats.inProgress = this.tasks.filter(t => t.status === 'in_progress').length;
			this.stats.completed = this.tasks.filter(t => t.status === 'completed').length;
			console.log('检修统计更新:', this.stats);
		},
		
		showAddDialog() {
			this.isEdit = false;
			this.taskForm = {
				id: null,
				title: '',
				description: '',
				deviceId: '',
				assignee: '',
				status: 'pending',
				deadline: ''
			};
			this.statusIndex = 0;
			this.showDialog = true;
		},
		
		editTask(task) {
			this.isEdit = true;
			this.taskForm = { ...task };
			
			// 设置状态选择器
			const statusIndexMap = {
				'pending': 0,
				'in_progress': 1,
				'completed': 2,
				'cancelled': 3
			};
			this.statusIndex = statusIndexMap[task.status] || 0;
			
			this.showDialog = true;
			console.log('编辑任务:', task);
		},
		
		onStatusChange(e) {
			this.statusIndex = e.detail.value;
			const statusMap = ['pending', 'in_progress', 'completed', 'cancelled'];
			this.taskForm.status = statusMap[this.statusIndex];
		},
		
		onDateChange(e) {
			this.taskForm.deadline = e.detail.value;
		},
		
		closeDialog() {
			this.showDialog = false;
			this.taskForm = {
				id: null,
				title: '',
				description: '',
				deviceId: '',
				assignee: '',
				status: 'pending',
				deadline: ''
			};
		},
		
		async saveTask() {
			if (!this.taskForm.title.trim()) {
				uni.showToast({
					title: '请输入任务标题',
					icon: 'none'
				});
				return;
			}
			
			if (!this.taskForm.description.trim()) {
				uni.showToast({
					title: '请输入任务描述',
					icon: 'none'
				});
				return;
			}
			
			if (!this.taskForm.deviceId.trim()) {
				uni.showToast({
					title: '请输入设备ID',
					icon: 'none'
				});
				return;
			}
			
			if (!this.taskForm.assignee.trim()) {
				uni.showToast({
					title: '请输入负责人',
					icon: 'none'
				});
				return;
			}
			
			this.saving = true;
			try {
				if (this.isEdit && this.taskForm.originalApplication) {
					// 更新真实的申请状态
					const newStatus = this.mapTaskStatusToApplicationStatus(this.taskForm.status);
					
					let apiUrl = '';
					let apiData = { id: this.taskForm.originalApplication.id };
					
					// 根据新状态选择不同的API
					if (newStatus === 'approved') {
						apiUrl = 'http://localhost:5050/api/mp/approve-application';
					} else if (newStatus === 'rejected') {
						apiUrl = 'http://localhost:5050/api/mp/reject-application';
					} else if (newStatus === 'completed') {
						apiUrl = 'http://localhost:5050/api/mp/approve-power-on';
					}
					
					if (apiUrl) {
						const response = await uni.request({
							url: apiUrl,
							method: 'POST',
							header: {
								'Content-Type': 'application/json'
							},
							data: apiData,
							timeout: 10000
						});
						
						if (response.statusCode === 200) {
							uni.showToast({
								title: '状态更新成功',
								icon: 'success'
							});
							this.closeDialog();
							this.fetchTasks(); // 重新获取数据
						} else {
							uni.showToast({
								title: '状态更新失败',
								icon: 'none'
							});
						}
					} else {
						uni.showToast({
							title: '不支持的状态更新',
							icon: 'none'
						});
					}
				} else {
					// 新建任务（这里可以添加新的申请）
					uni.showToast({
						title: '新建功能开发中',
						icon: 'none'
					});
				}
			} catch (err) {
				console.error('保存失败:', err);
				uni.showToast({
					title: '网络错误',
					icon: 'none'
				});
			} finally {
				this.saving = false;
			}
		},
		
		mapTaskStatusToApplicationStatus(taskStatus) {
			const statusMap = {
				'pending': 'pending',
				'in_progress': 'approved',
				'completed': 'completed',
				'cancelled': 'rejected'
			};
			return statusMap[taskStatus] || 'pending';
		},
		
		async deleteTask(taskId) {
			uni.showModal({
				title: '确认删除',
				content: '确定要删除这个任务吗？',
				success: (res) => {
					if (res.confirm) {
						// 模拟删除操作
						this.tasks = this.tasks.filter(t => t.id !== taskId);
						this.updateStats();
						uni.showToast({
							title: '任务删除成功',
							icon: 'success'
						});
					}
				}
			});
		},
		
		viewTask(task) {
			uni.showModal({
				title: task.title,
				content: `设备ID: ${task.deviceId}\n负责人: ${task.assignee}\n状态: ${this.getStatusText(task.status)}\n描述: ${task.description}`,
				showCancel: false
			});
		},
		
		goBack() {
			uni.navigateBack();
		}
	}
}
</script>

<style scoped>
.repair-container {
	min-height: 100vh;
	background: #f5f7fa;
}

.header {
	background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
	padding: 40rpx;
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.header-content {
	display: flex;
	align-items: center;
}

.logo-icon {
	width: 80rpx;
	height: 80rpx;
	background: rgba(255, 255, 255, 0.2);
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 20rpx;
}

.icon {
	font-size: 40rpx;
}

.header-text {
	display: flex;
	flex-direction: column;
}

.title {
	font-size: 36rpx;
	font-weight: bold;
	color: #fff;
}

.subtitle {
	font-size: 24rpx;
	color: rgba(255, 255, 255, 0.8);
	margin-top: 5rpx;
}

.back-btn {
	background: rgba(255, 255, 255, 0.2);
	border: none;
	border-radius: 10rpx;
	padding: 15rpx 25rpx;
	display: flex;
	align-items: center;
}

.back-icon {
	color: #fff;
	font-size: 28rpx;
	margin-right: 10rpx;
}

.back-btn text {
	color: #fff;
	font-size: 28rpx;
}

.content {
	padding: 40rpx;
}

.stats-container {
	display: flex;
	justify-content: space-between;
	margin-bottom: 40rpx;
}

.stat-card {
	background: #fff;
	border-radius: 15rpx;
	padding: 30rpx 20rpx;
	text-align: center;
	flex: 1;
	margin: 0 10rpx;
	box-shadow: 0 5rpx 15rpx rgba(0, 0, 0, 0.1);
}

.stat-value {
	display: block;
	font-size: 36rpx;
	font-weight: bold;
	color: #409eff;
	margin-bottom: 10rpx;
}

.stat-label {
	font-size: 24rpx;
	color: #666;
}

.task-list {
	background: #fff;
	border-radius: 15rpx;
	padding: 30rpx;
	box-shadow: 0 5rpx 15rpx rgba(0, 0, 0, 0.1);
}

.list-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 30rpx;
}

.list-title {
	font-size: 32rpx;
	font-weight: bold;
	color: #333;
}

.add-btn {
	background: #409eff;
	color: #fff;
	border: none;
	border-radius: 10rpx;
	padding: 15rpx 25rpx;
	font-size: 24rpx;
}

.loading, .empty {
	text-align: center;
	padding: 60rpx;
	color: #999;
	font-size: 28rpx;
}

.task-items {
	display: flex;
	flex-direction: column;
}

.task-item {
	background: #f8f9fa;
	border-radius: 10rpx;
	padding: 30rpx;
	margin-bottom: 20rpx;
	border-left: 5rpx solid #409eff;
}

.task-info {
	flex: 1;
}

.task-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 15rpx;
}

.task-title {
	font-size: 30rpx;
	font-weight: bold;
	color: #333;
}

.task-status {
	padding: 8rpx 15rpx;
	border-radius: 20rpx;
	font-size: 22rpx;
}

.status-pending {
	background: #fff3cd;
	color: #856404;
}

.status-in_progress {
	background: #d1ecf1;
	color: #0c5460;
}

.status-completed {
	background: #d4edda;
	color: #155724;
}

.status-cancelled {
	background: #f8d7da;
	color: #721c24;
}

.task-description {
	font-size: 26rpx;
	color: #666;
	margin-bottom: 15rpx;
	line-height: 1.5;
}

.task-meta {
	display: flex;
	gap: 30rpx;
	margin-bottom: 10rpx;
}

.task-device, .task-assignee {
	font-size: 24rpx;
	color: #999;
}

.task-time {
	display: flex;
	flex-direction: column;
	gap: 5rpx;
}

.task-date, .task-deadline {
	font-size: 22rpx;
	color: #999;
}

.task-actions {
	display: flex;
	gap: 15rpx;
	margin-top: 20rpx;
}

.action-btn {
	border: none;
	border-radius: 8rpx;
	padding: 15rpx 25rpx;
	font-size: 24rpx;
}

.edit-btn {
	background: #409eff;
	color: #fff;
}

.delete-btn {
	background: #f56c6c;
	color: #fff;
}

.task-dialog {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: rgba(0, 0, 0, 0.5);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 1000;
}

.dialog-content {
	background: #fff;
	border-radius: 20rpx;
	width: 80%;
	max-width: 600rpx;
	max-height: 80vh;
	overflow-y: auto;
}

.dialog-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 30rpx;
	border-bottom: 1rpx solid #f0f0f0;
}

.dialog-title {
	font-size: 32rpx;
	font-weight: bold;
	color: #333;
}

.close-btn {
	background: none;
	border: none;
	font-size: 40rpx;
	color: #999;
}

.dialog-form {
	padding: 30rpx;
}

.form-group {
	margin-bottom: 30rpx;
}

.label {
	display: block;
	font-size: 28rpx;
	color: #333;
	margin-bottom: 15rpx;
	font-weight: 500;
}

.input {
	width: 100%;
	height: 80rpx;
	border: 2rpx solid #e1e5e9;
	border-radius: 10rpx;
	padding: 0 20rpx;
	font-size: 28rpx;
	background: #f8f9fa;
	box-sizing: border-box;
}

.textarea {
	width: 100%;
	height: 120rpx;
	border: 2rpx solid #e1e5e9;
	border-radius: 10rpx;
	padding: 20rpx;
	font-size: 28rpx;
	background: #f8f9fa;
	box-sizing: border-box;
	resize: none;
}

.picker {
	width: 100%;
	height: 80rpx;
	border: 2rpx solid #e1e5e9;
	border-radius: 10rpx;
	background: #f8f9fa;
	display: flex;
	align-items: center;
	padding: 0 20rpx;
	box-sizing: border-box;
}

.picker-text {
	font-size: 28rpx;
	color: #333;
}

.dialog-buttons {
	display: flex;
	gap: 20rpx;
	padding: 30rpx;
	border-top: 1rpx solid #f0f0f0;
}

.save-btn, .cancel-btn {
	flex: 1;
	height: 80rpx;
	border: none;
	border-radius: 10rpx;
	font-size: 28rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.save-btn {
	background: #409eff;
	color: #fff;
}

.save-btn:disabled {
	background: #ccc;
}

.cancel-btn {
	background: #f5f5f5;
	color: #666;
}
</style> 