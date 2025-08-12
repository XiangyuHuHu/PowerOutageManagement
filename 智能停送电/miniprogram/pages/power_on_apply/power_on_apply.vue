<template>
  <view class="container">
    <view class="title">送电申请</view>
    <view v-if="loading" class="loading">加载中...</view>
    <view v-else>
      <view v-if="list.length === 0" class="empty">暂无可送电的申请</view>
      <view v-else>
        <view v-for="item in list" :key="item.id" class="item">
          <view class="row"><text class="label">设备编号：</text>{{ item.deviceId }}</view>
          <view class="row"><text class="label">停电原因：</text>{{ item.reason }}</view>
          <view class="row"><text class="label">申请人：</text>{{ item.applicant }}</view>
          <view class="row"><text class="label">时间：</text>{{ formatDateTime(item.created_at) }}</view>
          <button type="primary" @click="applyPowerOn(item.id)" :disabled="item.status==='power_on_applied'">{{ item.status==='power_on_applied' ? '已申请送电' : '申请送电' }}</button>
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
    year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
  });
};
const fetchList = async () => {
  loading.value = true;
  try {
    const res = await uni.request({ 
      url: 'http://localhost:5050/api/mp/applications', 
      method: 'GET',
      timeout: 10000
    });
    // 只显示当前电工可操作的申请
    list.value = (res.data || []).filter(app =>
      ['approved','verified','repairing','repair_completed'].includes(app.status) &&
      app.applicant === user.realname // 只显示自己的
    );
  } catch (e) { 
    console.error('获取申请列表失败:', e);
    list.value = []; 
  } finally { 
    loading.value = false; 
  }
};
const applyPowerOn = async (id) => {
  uni.showLoading({ title: '提交中...' });
  try {
    const res = await uni.request({
      url: 'http://localhost:5050/api/mp/power-on-apply',
      method: 'POST',
      header: { 'Content-Type': 'application/json' },
      data: { id },
      timeout: 10000
    });
    if (res.statusCode === 200) {
      uni.showToast({ title: '送电申请已提交', icon: 'success' });
      fetchList();
    } else {
      uni.showToast({ title: res.data.msg || '提交失败', icon: 'none' });
    }
  } catch (err) {
    console.error('提交送电申请失败:', err);
    uni.showToast({ title: '网络错误', icon: 'none' });
  } finally { 
    uni.hideLoading(); 
  }
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