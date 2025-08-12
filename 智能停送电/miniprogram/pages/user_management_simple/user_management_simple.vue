<template>
	<view class="container">
		<view class="header">
			<text class="title">用户管理 (简化版)</text>
			<button @click="goBack" class="back-btn">返回</button>
		</view>
		
		<view class="content">
			<view v-if="loading" class="loading">
				<text>加载中...</text>
			</view>
			
			<view v-else class="user-list">
				<view v-for="user in users" :key="user.id" class="user-item">
					<text class="user-name">{{ user.realname }}</text>
					<text class="user-role">{{ user.role }}</text>
				</view>
			</view>
			
			<button @click="fetchUsers" class="refresh-btn">刷新</button>
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
		console.log('简化版用户管理页面加载');
		this.fetchUsers();
	},
	
	methods: {
		goBack() {
			uni.navigateBack();
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
				
				console.log('响应:', response);
				
				if (response.statusCode === 200) {
					this.users = response.data;
					console.log('获取到', this.users.length, '个用户');
				} else {
					console.error('请求失败:', response.statusCode);
				}
			} catch (err) {
				console.error('网络错误:', err);
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
}

.header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 20rpx;
	background: #f0f0f0;
	margin-bottom: 20rpx;
}

.title {
	font-size: 32rpx;
	font-weight: bold;
}

.back-btn {
	background: #007AFF;
	color: white;
	padding: 10rpx 20rpx;
	border-radius: 10rpx;
}

.content {
	padding: 20rpx;
}

.loading {
	text-align: center;
	padding: 40rpx;
}

.user-list {
	margin-bottom: 40rpx;
}

.user-item {
	display: flex;
	justify-content: space-between;
	padding: 20rpx;
	border-bottom: 1rpx solid #eee;
}

.user-name {
	font-size: 28rpx;
}

.user-role {
	font-size: 24rpx;
	color: #666;
}

.refresh-btn {
	background: #007AFF;
	color: white;
	padding: 20rpx;
	border-radius: 10rpx;
	width: 100%;
}
</style> 