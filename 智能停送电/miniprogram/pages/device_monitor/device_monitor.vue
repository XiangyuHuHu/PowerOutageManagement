<template>
	<view class="container">
		<view class="header">
			<text class="title">设备监控</text>
			<button @click="goBack" class="back-btn">返回</button>
		</view>
		
		<view class="content">
			<!-- 设备状态概览 -->
			<view class="overview">
				<view class="overview-item">
					<text class="overview-value">{{ deviceCount }}</text>
					<text class="overview-label">在线设备</text>
				</view>
				<view class="overview-item">
					<text class="overview-value">{{ alertCount }}</text>
					<text class="overview-label">告警设备</text>
				</view>
			</view>
			
			<!-- 设备列表 -->
			<view class="device-list">
				<view class="list-header">
					<text class="list-title">设备状态</text>
					<button @click="refreshDevices" class="refresh-btn" :disabled="loading">
						{{ loading ? '刷新中...' : '刷新' }}
					</button>
				</view>
				
				<view v-if="loading" class="loading">
					<text>加载中...</text>
				</view>
				
				<view v-else-if="devices.length === 0" class="empty">
					<text>暂无设备数据</text>
				</view>
				
				<view v-else class="devices">
					<view v-for="device in devices" :key="device.device_id" class="device-item" @click="viewDeviceDetail(device)">
						<view class="device-info">
							<text class="device-name">{{ device.device_id }}</text>
							<text class="device-status" :class="getStatusClass(device.status.status)">
								{{ getStatusText(device.status.status) }}
							</text>
						</view>
						<view class="device-time">
							<text class="time-text">{{ formatTime(device.status.last_update) }}</text>
						</view>
					</view>
				</view>
			</view>
			
			<!-- 告警列表 -->
			<view v-if="alerts.length > 0" class="alert-list">
				<view class="list-header">
					<text class="list-title">设备告警</text>
				</view>
				<view class="alerts">
					<view v-for="alert in alerts" :key="alert.device_id" class="alert-item">
						<view class="alert-info">
							<text class="alert-device">{{ alert.device_id }}</text>
							<text class="alert-message">{{ alert.message }}</text>
						</view>
						<view class="alert-time">
							<text class="time-text">{{ formatTime(alert.timestamp) }}</text>
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
			devices: [],
			alerts: [],
			loading: false,
			deviceCount: 0,
			alertCount: 0
		}
	},
	
	onLoad() {
		console.log('设备监控页面加载');
		this.refreshDevices();
	},
	
	methods: {
		goBack() {
			uni.navigateBack();
		},
		
		getStatusText(status) {
			const statusMap = {
				'online': '在线',
				'offline': '离线',
				'error': '错误',
				'overload': '过载',
				'temperature_high': '温度过高',
				'voltage_high': '电压过高',
				'voltage_low': '电压过低',
				'unknown': '未知'
			};
			return statusMap[status] || status;
		},
		
		getStatusClass(status) {
			const classMap = {
				'online': 'status-online',
				'offline': 'status-offline',
				'error': 'status-error',
				'overload': 'status-warning',
				'temperature_high': 'status-warning',
				'voltage_high': 'status-warning',
				'voltage_low': 'status-warning'
			};
			return classMap[status] || 'status-unknown';
		},
		
		formatTime(timestamp) {
			if (!timestamp) return '未知时间';
			const date = new Date(timestamp * 1000);
			return date.toLocaleString('zh-CN');
		},
		
		async refreshDevices() {
			console.log('刷新设备状态');
			this.loading = true;
			
			try {
				const response = await uni.request({
					url: 'http://localhost:5050/api/mp/device-status',
					method: 'GET',
					timeout: 10000
				});
				
				if (response.statusCode === 200) {
					const devicesData = response.data.devices;
					this.devices = Object.keys(devicesData).map(deviceId => ({
						device_id: deviceId,
						status: devicesData[deviceId]
					}));
					this.deviceCount = this.devices.length;
					console.log('设备状态获取成功，共', this.deviceCount, '个设备');
				} else {
					console.error('获取设备状态失败，状态码:', response.statusCode);
				}
			} catch (err) {
				console.error('获取设备状态失败:', err);
			}
			
			// 获取告警信息
			try {
				const alertResponse = await uni.request({
					url: 'http://localhost:5050/api/mp/device-alerts',
					method: 'GET',
					timeout: 10000
				});
				
				if (alertResponse.statusCode === 200) {
					this.alerts = alertResponse.data.alerts;
					this.alertCount = this.alerts.length;
					console.log('告警信息获取成功，共', this.alertCount, '个告警');
				}
			} catch (err) {
				console.error('获取告警信息失败:', err);
			}
			
			this.loading = false;
		},
		
		viewDeviceDetail(device) {
			// 可以跳转到设备详情页面
			uni.showModal({
				title: '设备详情',
				content: `设备ID: ${device.device_id}\n状态: ${this.getStatusText(device.status.status)}\n最后更新: ${this.formatTime(device.status.last_update)}`,
				showCancel: false
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

.overview {
	display: flex;
	gap: 20rpx;
	margin-bottom: 30rpx;
}

.overview-item {
	flex: 1;
	background: #fff;
	padding: 30rpx;
	border-radius: 15rpx;
	text-align: center;
	box-shadow: 0 2rpx 10rpx rgba(0,0,0,0.1);
}

.overview-value {
	display: block;
	font-size: 36rpx;
	font-weight: bold;
	color: #007AFF;
	margin-bottom: 10rpx;
}

.overview-label {
	font-size: 24rpx;
	color: #666;
}

.device-list, .alert-list {
	background: #fff;
	border-radius: 15rpx;
	padding: 20rpx;
	margin-bottom: 20rpx;
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

.device-item, .alert-item {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 20rpx;
	border-bottom: 1rpx solid #eee;
}

.device-item:last-child, .alert-item:last-child {
	border-bottom: none;
}

.device-info, .alert-info {
	flex: 1;
}

.device-name, .alert-device {
	display: block;
	font-size: 28rpx;
	font-weight: bold;
	color: #333;
	margin-bottom: 5rpx;
}

.device-status {
	display: block;
	font-size: 22rpx;
	padding: 4rpx 12rpx;
	border-radius: 10rpx;
	width: fit-content;
}

.status-online {
	background: #d4edda;
	color: #155724;
}

.status-offline {
	background: #f8d7da;
	color: #721c24;
}

.status-error {
	background: #f8d7da;
	color: #721c24;
}

.status-warning {
	background: #fff3cd;
	color: #856404;
}

.status-unknown {
	background: #e2e3e5;
	color: #383d41;
}

.alert-message {
	display: block;
	font-size: 24rpx;
	color: #dc3545;
}

.device-time, .alert-time {
	text-align: right;
}

.time-text {
	font-size: 22rpx;
	color: #999;
}
</style> 