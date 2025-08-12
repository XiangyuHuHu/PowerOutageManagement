<template>
	<view class="stats-container">
		<view class="header">
			<view class="header-content">
				<view class="logo-icon">
					<text class="icon">📊</text>
				</view>
				<view class="header-text">
					<text class="title">系统统计</text>
					<text class="subtitle">智能停送电系统数据分析</text>
				</view>
			</view>
			<button class="back-btn" @click="goBack">
				<text class="back-icon">←</text>
				<text>返回</text>
			</button>
		</view>
		
		<view class="content">
			<view v-if="loading" class="loading">
				<text class="loading-text">加载统计数据...</text>
			</view>
			
			<view v-else class="stats-content">
				<!-- 统计卡片 -->
				<view class="stats-grid">
					<view class="stat-card">
						<view class="stat-icon" style="color: #409eff;">
							<text class="icon">📝</text>
						</view>
						<text class="stat-value">{{ stats.totalApplications }}</text>
						<text class="stat-label">总申请数</text>
						<view class="stat-trend trend-up">
							<text class="trend-icon">↗</text>
							<text class="trend-text">+{{ stats.newApplications }} 今日新增</text>
						</view>
					</view>
					
					<view class="stat-card">
						<view class="stat-icon" style="color: #67c23a;">
							<text class="icon">✅</text>
						</view>
						<text class="stat-value">{{ stats.approvedApplications }}</text>
						<text class="stat-label">已审批</text>
						<view class="stat-trend trend-up">
							<text class="trend-icon">↗</text>
							<text class="trend-text">{{ stats.approvalRate }}% 审批率</text>
						</view>
					</view>
					
					<view class="stat-card">
						<view class="stat-icon" style="color: #e6a23c;">
							<text class="icon">⏳</text>
						</view>
						<text class="stat-value">{{ stats.pendingApplications }}</text>
						<text class="stat-label">待审批</text>
						<view class="stat-trend trend-down">
							<text class="trend-icon">↘</text>
							<text class="trend-text">需要处理</text>
						</view>
					</view>
					
					<view class="stat-card">
						<view class="stat-icon" style="color: #f56c6c;">
							<text class="icon">👥</text>
						</view>
						<text class="stat-value">{{ stats.totalUsers }}</text>
						<text class="stat-label">注册用户</text>
						<view class="stat-trend trend-up">
							<text class="trend-icon">↗</text>
							<text class="trend-text">+{{ stats.activeUsers }} 活跃用户</text>
						</view>
					</view>
				</view>
				
				<!-- 图表区域 -->
				<view class="chart-grid">
					<view class="chart-container">
						<view class="chart-title">
							<text class="icon">📊</text>
							<text>申请状态分布</text>
						</view>
						<view class="chart-content">
							<view class="chart-item">
								<text class="chart-label">已审批</text>
								<text class="chart-value">{{ stats.approvedApplications }}</text>
							</view>
							<view class="chart-item">
								<text class="chart-label">待审批</text>
								<text class="chart-value">{{ stats.pendingApplications }}</text>
							</view>
							<view class="chart-item">
								<text class="chart-label">已拒绝</text>
								<text class="chart-value">{{ stats.rejectedApplications }}</text>
							</view>
						</view>
					</view>
					
					<view class="chart-container">
						<view class="chart-title">
							<text class="icon">👥</text>
							<text>用户角色分布</text>
						</view>
						<view class="chart-content">
							<view class="chart-item">
								<text class="chart-label">管理员</text>
								<text class="chart-value">{{ stats.adminUsers }}</text>
							</view>
							<view class="chart-item">
								<text class="chart-label">调度员</text>
								<text class="chart-value">{{ stats.dispatcherUsers }}</text>
							</view>
							<view class="chart-item">
								<text class="chart-label">电工</text>
								<text class="chart-value">{{ stats.electricianUsers }}</text>
							</view>
						</view>
					</view>
				</view>
				
				<!-- 最近活动 -->
				<view class="recent-activity">
					<view class="activity-header">
						<text class="icon">📋</text>
						<text class="activity-title">最近活动</text>
					</view>
					
					<view v-if="recentActivities.length === 0" class="empty-activity">
						<text>暂无活动记录</text>
					</view>
					
					<view v-else class="activity-list">
						<view 
							v-for="activity in recentActivities" 
							:key="activity.id" 
							class="activity-item"
						>
							<view class="activity-icon" :style="{ background: getActivityColor(activity.type) }">
								<text class="icon">{{ getActivityIcon(activity.type) }}</text>
							</view>
							<view class="activity-content">
								<text class="activity-title">{{ activity.title }}</text>
								<text class="activity-time">{{ formatDateTime(activity.time) }}</text>
							</view>
						</view>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
export default {
	data() {
		return {
			loading: true,
			stats: {
				totalApplications: 0,
				approvedApplications: 0,
				pendingApplications: 0,
				rejectedApplications: 0,
				newApplications: 0,
				approvalRate: 0,
				totalUsers: 0,
				activeUsers: 0,
				adminUsers: 0,
				dispatcherUsers: 0,
				electricianUsers: 0
			},
			recentActivities: []
		}
	},
	
	onLoad() {
		this.checkPermission();
		this.fetchStats();
	},
	
	methods: {
		checkPermission() {
			const userRole = uni.getStorageSync('user_role');
			if (userRole !== 'admin') {
				uni.showToast({
					title: '只有管理员可以访问统计页面',
					icon: 'none'
				});
				uni.navigateBack();
			}
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
				month: '2-digit',
				day: '2-digit',
				hour: '2-digit',
				minute: '2-digit'
			});
		},
		
		getActivityColor(type) {
			const colors = {
				'apply': 'linear-gradient(135deg, #409eff, #2a6bc5)',
				'approve': 'linear-gradient(135deg, #67c23a, #4a8c2c)',
				'reject': 'linear-gradient(135deg, #f56c6c, #c45656)',
				'user': 'linear-gradient(135deg, #e6a23c, #b88230)'
			};
			return colors[type] || colors['apply'];
		},
		
		getActivityIcon(type) {
			const icons = {
				'apply': '📝',
				'approve': '✅',
				'reject': '❌',
				'user': '👤'
			};
			return icons[type] || '📋';
		},
		
		async fetchStats() {
			try {
				// 获取统计数据
				const statsRes = await uni.request({
					url: 'http://localhost:5050/api/mp/stats',
					method: 'GET',
					header: {
						'Content-Type': 'application/json'
					},
					timeout: 10000 // 10秒超时
				});
				
				// 获取申请数据用于详细统计
				const applicationsRes = await uni.request({
					url: 'http://localhost:5050/api/mp/applications',
					method: 'GET',
					header: {
						'Content-Type': 'application/json'
					},
					timeout: 10000 // 10秒超时
				});
				
				if (statsRes.statusCode === 200 && applicationsRes.statusCode === 200) {
					const stats = statsRes.data;
					const applications = applicationsRes.data;
					
					// 计算统计数据
					this.stats.totalApplications = stats.applications;
					this.stats.totalUsers = stats.users;
					
					// 从申请数据计算详细统计
					this.stats.approvedApplications = applications.filter(app => app.status === 'approved').length;
					this.stats.pendingApplications = applications.filter(app => app.status === 'pending').length;
					this.stats.rejectedApplications = applications.filter(app => app.status === 'rejected').length;
					
					// 计算审批率
					const totalProcessed = this.stats.approvedApplications + this.stats.rejectedApplications;
					this.stats.approvalRate = totalProcessed > 0 ? Math.round((this.stats.approvedApplications / totalProcessed) * 100) : 0;
					
					// 今日新增申请（简化计算）
					const today = new Date();
					const todayApplications = applications.filter(app => {
						const appDate = new Date(app.created_at);
						return appDate.toDateString() === today.toDateString();
					});
					this.stats.newApplications = todayApplications.length;
					
					// 用户角色统计
					this.stats.adminUsers = stats.role_stats.admin || 0;
					this.stats.dispatcherUsers = stats.role_stats.dispatcher || 0;
					this.stats.electricianUsers = stats.role_stats.electrician || 0;
					this.stats.activeUsers = stats.users; // 简化计算
					
					// 生成最近活动（基于申请数据）
					this.recentActivities = applications.slice(0, 5).map(app => ({
						id: app.id,
						type: app.status === 'approved' ? 'approve' : app.status === 'rejected' ? 'reject' : 'apply',
						title: `${app.applicant_name || '未知用户'} 提交了${app.type === 'power_off' ? '停电' : '送电'}申请`,
						time: app.created_at
					}));
				} else {
					uni.showToast({
						title: '获取统计数据失败',
						icon: 'none'
					});
				}
			} catch (err) {
				console.error('获取统计数据失败：', err);
				uni.showToast({
					title: '网络错误',
					icon: 'none'
				});
			} finally {
				this.loading = false;
			}
		},
		
		goBack() {
			uni.navigateBack();
		}
	}
}
</script>

<style scoped>
.stats-container {
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

.loading {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 100rpx 0;
}

.loading-text {
	font-size: 28rpx;
	color: #999;
	margin-top: 20rpx;
}

.stats-content {
	display: flex;
	flex-direction: column;
	gap: 40rpx;
}

.stats-grid {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 20rpx;
}

.stat-card {
	background: #fff;
	border-radius: 15rpx;
	padding: 30rpx;
	box-shadow: 0 5rpx 15rpx rgba(0, 0, 0, 0.1);
	display: flex;
	flex-direction: column;
	align-items: center;
}

.stat-icon {
	margin-bottom: 15rpx;
}

.stat-value {
	font-size: 48rpx;
	font-weight: bold;
	color: #333;
	margin-bottom: 10rpx;
}

.stat-label {
	font-size: 24rpx;
	color: #666;
	margin-bottom: 15rpx;
}

.stat-trend {
	display: flex;
	align-items: center;
	font-size: 22rpx;
}

.trend-up {
	color: #67c23a;
}

.trend-down {
	color: #f56c6c;
}

.trend-icon {
	margin-right: 5rpx;
}

.trend-text {
	font-size: 20rpx;
}

.chart-grid {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 20rpx;
}

.chart-container {
	background: #fff;
	border-radius: 15rpx;
	padding: 30rpx;
	box-shadow: 0 5rpx 15rpx rgba(0, 0, 0, 0.1);
}

.chart-title {
	display: flex;
	align-items: center;
	margin-bottom: 30rpx;
	font-size: 28rpx;
	font-weight: bold;
	color: #333;
}

.chart-title .icon {
	margin-right: 10rpx;
}

.chart-content {
	display: flex;
	flex-direction: column;
	gap: 20rpx;
}

.chart-item {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 20rpx 0;
	border-bottom: 1rpx solid #f0f0f0;
}

.chart-item:last-child {
	border-bottom: none;
}

.chart-label {
	font-size: 26rpx;
	color: #666;
}

.chart-value {
	font-size: 28rpx;
	font-weight: bold;
	color: #409eff;
}

.recent-activity {
	background: #fff;
	border-radius: 15rpx;
	padding: 30rpx;
	box-shadow: 0 5rpx 15rpx rgba(0, 0, 0, 0.1);
}

.activity-header {
	display: flex;
	align-items: center;
	margin-bottom: 30rpx;
	font-size: 28rpx;
	font-weight: bold;
	color: #333;
}

.activity-header .icon {
	margin-right: 10rpx;
}

.empty-activity {
	text-align: center;
	padding: 60rpx;
	color: #999;
	font-size: 28rpx;
}

.activity-list {
	display: flex;
	flex-direction: column;
	gap: 20rpx;
}

.activity-item {
	display: flex;
	align-items: center;
	padding: 20rpx 0;
	border-bottom: 1rpx solid #f0f0f0;
}

.activity-item:last-child {
	border-bottom: none;
}

.activity-icon {
	width: 60rpx;
	height: 60rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 20rpx;
}

.activity-icon .icon {
	font-size: 24rpx;
	color: #fff;
}

.activity-content {
	flex: 1;
	display: flex;
	flex-direction: column;
}

.activity-title {
	font-size: 26rpx;
	color: #333;
	margin-bottom: 5rpx;
}

.activity-time {
	font-size: 22rpx;
	color: #999;
}

/* 响应式设计 */
@media (max-width: 750rpx) {
	.stats-grid {
		grid-template-columns: 1fr;
	}
	
	.chart-grid {
		grid-template-columns: 1fr;
	}
	
	.content {
		padding: 20rpx;
	}
}
</style> 