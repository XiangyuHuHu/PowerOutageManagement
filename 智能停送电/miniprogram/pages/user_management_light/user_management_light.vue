<template>
	<view class="container">
		<view class="header">
			<text class="title">用户管理</text>
			<button @click="goBack" class="back-btn">返回</button>
		</view>
		
		<view class="content">
			<!-- 加载状态 -->
			<view v-if="loading" class="loading">
				<text>加载中...</text>
			</view>
			
			<!-- 用户列表 -->
			<view v-else class="user-list">
				<view v-for="user in users" :key="user.id" class="user-item">
					<view class="user-info">
						<text class="user-name">{{ user.realname }}</text>
						<text class="user-username">@{{ user.username }}</text>
						<text class="user-role">{{ getRoleText(user.role) }}</text>
					</view>
				</view>
			</view>
			
			<!-- 统计信息 -->
			<view v-if="!loading && users.length > 0" class="stats">
				<text class="stats-text">共 {{ users.length }} 个用户</text>
			</view>
			
			<!-- 刷新按钮 -->
			<button @click="fetchUsers" class="refresh-btn" :disabled="loading">
				{{ loading ? '刷新中...' : '刷新' }}
			</button>
		</view>
	</view>
</template>

<script>
export default {
	data() {
		return {
			users: [],
			loading: false
		}
	},
	
	onLoad() {
		console.log('轻量级用户管理页面加载');
		// 延迟加载，避免页面跳转超时
		setTimeout(() => {
			this.fetchUsers();
		}, 500);
	},
	
	methods: {
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
					timeout: 10000
				});
				
				console.log('用户列表响应:', response);
				
				if (response.statusCode === 200) {
					this.users = response.data;
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

.loading {
	text-align: center;
	padding: 40rpx;
	color: #666;
}

.user-list {
	background: #fff;
	border-radius: 15rpx;
	padding: 20rpx;
	margin-bottom: 20rpx;
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

.stats {
	text-align: center;
	padding: 20rpx;
	background: #fff;
	border-radius: 15rpx;
	margin-bottom: 20rpx;
}

.stats-text {
	font-size: 28rpx;
	color: #666;
}

.refresh-btn {
	background: #28a745;
	color: white;
	padding: 20rpx;
	border-radius: 10rpx;
	font-size: 28rpx;
	width: 100%;
}
</style> 