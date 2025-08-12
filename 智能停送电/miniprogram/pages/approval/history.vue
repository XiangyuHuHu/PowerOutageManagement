<template>
  <view class="history-container">
    <view class="title">历史记录</view>
    <view v-if="loading" class="loading">加载中...</view>
    <view v-else>
      <view v-if="historyList.length === 0" class="empty">暂无历史记录</view>
      <view v-else>
        <view v-for="item in historyList" :key="item.id" class="history-item" @click="viewDetail(item.id)">
          <view class="row">
            <text class="label">申请人：</text><text>{{ item.applicant }}</text>
          </view>
          <view class="row">
            <text class="label">设备编号：</text><text>{{ item.device_id }}</text>
          </view>
          <view class="row">
            <text class="label">停电原因：</text><text>{{ item.reason }}</text>
          </view>
          <view class="row">
            <text class="label">时间：</text><text>{{ formatDateTime(item.created_at) }}</text>
          </view>
          <view class="row">
            <text class="label">当前状态：</text><text>{{ statusText(item.status) }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue';
const historyList = ref([]);
const loading = ref(false);
const user = uni.getStorageSync('user') || {};
const statusMap = {
  pending: "待审批",
  approved: "审批通过",
  rejected: "审批驳回",
  verified: "已验电",
  "verify-rejected": "验电驳回",
  repairing: "检修中",
  repair_completed: "检修完成",
  power_on_applied: "送电申请",
  completed: "已完成",
  power_on_rejected: "送电驳回"
};
const statusText = (status) => statusMap[status] || status;
const formatDateTime = (timestamp) => {
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
};
const fetchHistory = async () => {
  loading.value = true;
  try {
    const res = await uni.request({
      url: `http://localhost:5050/api/mp/my-applications?applicant=${encodeURIComponent(user.realname || user.username)}`,
      method: 'GET',
      timeout: 10000
    });
    // 只排除"pending"和"power_on_applied"状态
    historyList.value = (res.data || []).filter(app => !['pending', 'power_on_applied'].includes(app.status));
  } catch (err) {
    console.error('获取历史记录失败:', err);
    historyList.value = [];
  } finally {
    loading.value = false;
  }
};
const viewDetail = (id) => {
  uni.navigateTo({ url: `/pages/approval/detail?id=${id}` });
};
onMounted(() => {
  fetchHistory();
});
</script>

<style scoped>
.history-container { padding: 24rpx; }
.title { font-size: 40rpx; font-weight: bold; margin-bottom: 32rpx; }
.loading, .empty { text-align: center; color: #888; margin: 40rpx 0; }
.history-item { background: #22384a; border-radius: 16rpx; margin-bottom: 24rpx; padding: 24rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.08); }
.row { margin-bottom: 10rpx; font-size: 28rpx; }
.label { color: #90caf9; margin-right: 12rpx; }
</style> 