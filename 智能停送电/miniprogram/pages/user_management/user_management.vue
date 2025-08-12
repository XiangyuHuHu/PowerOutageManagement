<template>
	<view class="container">
		<view class="header">
			<text class="title">用户管理</text>
			<button @click="goBack" class="back-btn">返回</button>
		</view>
		
		<view class="content">
			<!-- 统计信息 -->
			<view class="stats">
				<view class="stat-item">
					<text class="stat-value">{{ stats.total }}</text>
					<text class="stat-label">总用户</text>
				</view>
				<view class="stat-item">
					<text class="stat-value">{{ stats.admin }}</text>
					<text class="stat-label">管理员</text>
				</view>
				<view class="stat-item">
					<text class="stat-value">{{ stats.dispatcher }}</text>
					<text class="stat-label">调度员</text>
				</view>
				<view class="stat-item">
					<text class="stat-value">{{ stats.electrician }}</text>
					<text class="stat-label">电工</text>
				</view>
			</view>
			
			<!-- 用户列表 -->
			<view class="user-list">
				<view class="list-header">
					<text class="list-title">用户列表</text>
					<button @click="fetchUsers" class="refresh-btn" :disabled="loading">
						{{ loading ? '刷新中...' : '刷新' }}
					</button>
				</view>
				
				<view v-if="loading" class="loading">
					<text>加载中...</text>
				</view>
				
				<view v-else-if="users.length === 0" class="empty">
					<text>暂无用户数据</text>
				</view>
				
				<view v-else class="users">
					<view v-for="user in users" :key="user.id" class="user-item">
						<view class="user-info">
							<text class="user-name">{{ user.realname }}</text>
							<text class="user-username">@{{ user.username }}</text>
							<text class="user-role">{{ getRoleText(user.role) }}</text>
						</view>
						<view class="user-actions">
							<button class="edit-btn" @click="editUser(user)">编辑</button>
							<button v-if="user.role !== 'admin'" class="delete-btn" @click="deleteUser(user.id)">删除</button>
						</view>
					</view>
				</view>
			</view>
		</view>
		
		<!-- 编辑弹窗 -->
		<view v-if="showEditDialog" class="dialog-overlay" @click="closeEditDialog">
			<view class="dialog" @click.stop>
				<view class="dialog-header">
					<text class="dialog-title">编辑用户</text>
					<button class="close-btn" @click="closeEditDialog">×</button>
				</view>
				
				<view class="dialog-content">
					<view class="form-item">
						<text class="label">用户名</text>
						<input class="input" v-model="editForm.username" placeholder="请输入用户名" />
					</view>
					
					<view class="form-item">
						<text class="label">真实姓名</text>
						<input class="input" v-model="editForm.realname" placeholder="请输入真实姓名" />
					</view>
					
					<view class="form-item">
						<text class="label">角色</text>
						<picker class="picker" :value="editRoleIndex" :range="roleOptions" @change="onEditRoleChange">
							<text class="picker-text">{{ roleOptions[editRoleIndex] }}</text>
						</picker>
					</view>
					
					<view class="form-item">
						<text class="label">新密码（留空则不修改）</text>
						<input class="input" v-model="editForm.password" type="password" placeholder="请输入新密码" />
					</view>
				</view>
				
				<view class="dialog-footer">
					<button class="cancel-btn" @click="closeEditDialog">取消</button>
					<button class="save-btn" @click="saveUser" :disabled="saving">
						{{ saving ? '保存中...' : '保存' }}
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
			users: [],
			loading: false,
			stats: {
				total: 0,
				admin: 0,
				dispatcher: 0,
				electrician: 0
			},
			showEditDialog: false,
			editForm: {
				id: null,
				username: '',
				realname: '',
				role: '',
				password: ''
			},
			roleOptions: ['管理员', '调度员', '电工', '普通用户'],
			editRoleIndex: 0,
			saving: false
		}
	},
	
	onLoad() {
		console.log('用户管理页面加载开始');
		// 延迟检查权限，避免页面跳转冲突
		setTimeout(() => {
			this.checkPermission();
		}, 200);
		// 延迟加载数据，避免页面跳转超时
		setTimeout(() => {
			this.fetchUsers();
		}, 1000);
	},
	
	onShow() {
		console.log('用户管理页面显示');
	},
	
	methods: {
		checkPermission() {
			const userRole = uni.getStorageSync('user_role');
			console.log('检查权限，用户角色:', userRole);
			if (userRole !== 'admin') {
				console.log('权限不足，用户角色不是admin');
				uni.showToast({
					title: '只有管理员可以访问用户管理页面',
					icon: 'none',
					duration: 2000
				});
				// 延迟返回，避免页面跳转冲突
				setTimeout(() => {
					console.log('执行navigateBack');
					uni.navigateBack();
				}, 500);
			} else {
				console.log('权限检查通过');
			}
		},
		
		goBack() {
			uni.navigateBack();
		},
		
		getRoleText(role) {
			const roleMap = {
				'admin': '管理员',
				'dispatcher': '调度员',
				'electrician': '电工',
				'user': '普通用户'
			};
			return roleMap[role] || role;
		},
		
		async fetchUsers() {
			console.log('开始获取用户列表');
			this.loading = true;
			try {
				const response = await uni.request({
					url: 'http://localhost:5050/api/mp/users',
					method: 'GET',
					header: {
						'Content-Type': 'application/json'
					},
					timeout: 15000
				});
				
				console.log('用户列表响应:', response);
				
				if (response.statusCode === 200) {
					this.users = response.data;
					this.updateStats();
					console.log('用户列表获取成功，共', this.users.length, '个用户');
				} else {
					console.error('获取用户列表失败，状态码:', response.statusCode);
					uni.showToast({
						title: '获取用户列表失败',
						icon: 'none'
					});
				}
			} catch (err) {
				console.error('获取用户列表失败:', err);
				uni.showToast({
					title: '网络错误',
					icon: 'none'
				});
			} finally {
				this.loading = false;
			}
		},
		
		updateStats() {
			this.stats.total = this.users.length;
			this.stats.admin = this.users.filter(u => u.role === 'admin').length;
			this.stats.dispatcher = this.users.filter(u => u.role === 'dispatcher').length;
			this.stats.electrician = this.users.filter(u => u.role === 'electrician').length;
		},
		
		editUser(user) {
			this.editForm = {
				id: user.id,
				username: user.username,
				realname: user.realname,
				role: user.role,
				password: ''
			};
			
			const roleIndexMap = {
				'admin': 0,
				'dispatcher': 1,
				'electrician': 2,
				'user': 3
			};
			this.editRoleIndex = roleIndexMap[user.role] || 0;
			
			this.showEditDialog = true;
		},
		
		onEditRoleChange(e) {
			this.editRoleIndex = e.detail.value;
			const roleMap = ['admin', 'dispatcher', 'electrician', 'user'];
			this.editForm.role = roleMap[this.editRoleIndex];
		},
		
		closeEditDialog() {
			this.showEditDialog = false;
			this.editForm = {
				id: null,
				username: '',
				realname: '',
				role: '',
				password: ''
			};
		},
		
		async saveUser() {
			if (!this.editForm.username || !this.editForm.realname) {
				uni.showToast({
					title: '请填写完整信息',
					icon: 'none'
				});
				return;
			}
			
			this.saving = true;
			try {
				// 暂时禁用编辑功能，因为需要认证的API
				uni.showToast({
					title: '编辑功能开发中',
					icon: 'none'
				});
				this.closeEditDialog();
			} catch (err) {
				console.error('保存用户失败:', err);
				uni.showToast({
					title: '网络错误',
					icon: 'none'
				});
			} finally {
				this.saving = false;
			}
		},
		
		async deleteUser(userId) {
			uni.showModal({
				title: '确认删除',
				content: '确定要删除这个用户吗？',
				success: async (res) => {
					if (res.confirm) {
						// 暂时禁用删除功能，因为需要认证的API
						uni.showToast({
							title: '删除功能开发中',
							icon: 'none'
						});
					}
				}
			});
		}
	}
}
</script>

<style>
.container {
	padding: 20rpx;
	background: #f5f7fa;
	min-height: 100vh;
}

.header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 20rpx;
	background: #fff;
	border-radius: 15rpx;
	margin-bottom: 20rpx;
}

.title {
	font-size: 32rpx;
	font-weight: bold;
	color: #333;
}

.back-btn {
	background: #007AFF;
	color: white;
	padding: 10rpx 20rpx;
	border-radius: 10rpx;
	font-size: 26rpx;
}

.content {
	padding: 20rpx;
}

.stats {
	display: grid;
	grid-template-columns: repeat(4, 1fr);
	gap: 20rpx;
	margin-bottom: 30rpx;
}

.stat-item {
	background: #fff;
	padding: 20rpx;
	border-radius: 10rpx;
	text-align: center;
	box-shadow: 0 2rpx 10rpx rgba(0,0,0,0.1);
}

.stat-value {
	display: block;
	font-size: 32rpx;
	font-weight: bold;
	color: #007AFF;
	margin-bottom: 5rpx;
}

.stat-label {
	font-size: 24rpx;
	color: #666;
}

.user-list {
	background: #fff;
	border-radius: 15rpx;
	padding: 20rpx;
}

.list-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20rpx;
}

.list-title {
	font-size: 28rpx;
	font-weight: bold;
	color: #333;
}

.refresh-btn {
	background: #28a745;
	color: white;
	padding: 10rpx 20rpx;
	border-radius: 8rpx;
	font-size: 24rpx;
}

.loading, .empty {
	text-align: center;
	padding: 40rpx;
	color: #666;
}

.user-item {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 20rpx;
	border-bottom: 1rpx solid #eee;
}

.user-item:last-child {
	border-bottom: none;
}

.user-info {
	flex: 1;
}

.user-name {
	display: block;
	font-size: 28rpx;
	font-weight: bold;
	color: #333;
	margin-bottom: 5rpx;
}

.user-username {
	display: block;
	font-size: 24rpx;
	color: #666;
	margin-bottom: 5rpx;
}

.user-role {
	display: block;
	font-size: 22rpx;
	color: #007AFF;
	background: #e3f2fd;
	padding: 4rpx 12rpx;
	border-radius: 10rpx;
	width: fit-content;
}

.user-actions {
	display: flex;
	gap: 10rpx;
}

.edit-btn, .delete-btn {
	padding: 8rpx 16rpx;
	border-radius: 6rpx;
	font-size: 24rpx;
}

.edit-btn {
	background: #007AFF;
	color: white;
}

.delete-btn {
	background: #dc3545;
	color: white;
}

.dialog-overlay {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: rgba(0,0,0,0.5);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 1000;
}

.dialog {
	background: #fff;
	border-radius: 15rpx;
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
	border-bottom: 1rpx solid #eee;
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

.dialog-content {
	padding: 30rpx;
}

.form-item {
	margin-bottom: 30rpx;
}

.label {
	display: block;
	font-size: 28rpx;
	color: #333;
	margin-bottom: 15rpx;
	font-weight: 500;
}

.input, .picker {
	width: 100%;
	height: 80rpx;
	border: 2rpx solid #e1e5e9;
	border-radius: 10rpx;
	padding: 0 20rpx;
	font-size: 28rpx;
	background: #f8f9fa;
	box-sizing: border-box;
}

.picker {
	display: flex;
	align-items: center;
}

.picker-text {
	font-size: 28rpx;
	color: #333;
}

.dialog-footer {
	display: flex;
	gap: 20rpx;
	padding: 30rpx;
	border-top: 1rpx solid #eee;
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
	background: #007AFF;
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