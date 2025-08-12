<template>
  <view class="container">
    <view class="title">我的申请 · 检修/操作</view>
    <view v-if="loading" class="loading">加载中...</view>
    <view v-else>
      <view v-if="list.length === 0" class="empty">暂无相关申请</view>
      <view v-else>
        <view v-for="item in list" :key="item.id" class="item" @click="viewDetail(item.id)">
          <view class="row"><text class="label">设备编号：</text>{{ item.deviceId }}</view>
          <view class="row"><text class="label">停电原因：</text>{{ item.reason }}</view>
          <view class="row"><text class="label">时间：</text>{{ formatDateTime(item.created_at) }}</view>
          <view class="row"><text class="label">当前状态：</text>{{ statusText(item.status) }}</view>
          <button v-if="canRepair(item)" type="primary" @click.stop="doRepair(item.id)">检修完成</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue';
const list = ref([]);
const loading = ref(false);
const user = uni.getStorageSync('user') || {};
const statusMap = {
  pending: "待审批", approved: "审批通过", rejected: "审批驳回", verified: "已验电", "verify-rejected": "验电驳回", repairing: "检修中", repair_completed: "检修完成", power_on_applied: "送电申请", completed: "已完成", power_on_rejected: "送电驳回"
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
  
  return date.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
};
const fetchList = async () => {
  loading.value = true;
  try {
    const res = await uni.request({ url: 'http://localhost:5050/api/list', method: 'GET', withCredentials: true });
    // 只显示当前电工相关的申请
    list.value = (res.data.data || res.data).filter(app => app.applicant === user.realname);
  } catch (e) { list.value = []; } finally { loading.value = false; }
};
const canRepair = (item) => ['repairing'].includes(item.status);
const doRepair = async (id) => {
  uni.showLoading({ title: '提交中...' });
  try {
    const res = await uni.request({
      url: 'http://localhost:5050/api/update-status',
      method: 'POST',
      data: { id, status: 'repair_completed' },
      withCredentials: true
    });
    if (res[1].statusCode === 200) {
      uni.showToast({ title: '检修完成', icon: 'success' });
      fetchList();
    } else {
      uni.showToast({ title: res[1].data.msg || '提交失败', icon: 'none' });
    }
  } finally { uni.hideLoading(); }
};
const viewDetail = (id) => {
  uni.navigateTo({ url: `/pages/approval/detail?id=${id}` });
};
onMounted(fetchList);
</script>

<style scoped>
.container { padding: 24rpx; }
.title { font-size: 40rpx; font-weight: bold; margin-bottom: 32rpx; }
.loading, .empty { text-align: center; color: #888; margin: 40rpx 0; }
.item { background: #22384a; border-radius: 16rpx; margin-bottom: 24rpx; padding: 24rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.08); }
.row { margin-bottom: 10rpx; font-size: 28rpx; }
.label { color: #90caf9; margin-right: 12rpx; }
</style>
