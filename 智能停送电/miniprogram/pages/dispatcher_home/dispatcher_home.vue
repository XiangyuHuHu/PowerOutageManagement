<template>
  <view class="main">
    <view class="title"><text class="icon">📋</text> 调度员工作台</view>
    <view class="btn-group">
      <button class="main-btn" @click="goApproval">
        <text class="icon">📝</text> 审批中心
      </button>
      <button class="main-btn" @click="goHistory">
        <text class="icon">📜</text> 历史记录
      </button>
      <button class="main-btn" @click="goStats">
        <text class="icon">📊</text> 统计分析
      </button>
    </view>
  </view>
</template>

<script setup>
const goApproval = () => {
  uni.navigateTo({ url: '/pages/approval/approval' });
};
const goHistory = () => {
  uni.navigateTo({ url: '/pages/approval/history' });
};
const goStats = () => {
  uni.showToast({ title: '敬请期待', icon: 'none' });
};
</script>

<style scoped>
.main {
  background: rgba(16,33,47,0.95);
  border-radius: 16rpx;
  padding: 48rpx 40rpx;
  box-shadow: 0 10rpx 30rpx rgba(0,0,0,0.4);
  margin: 40rpx auto;
  max-width: 600rpx;
}
.title {
  font-size: 44rpx;
  font-weight: bold;
  text-align: center;
  margin-bottom: 48rpx;
}
.btn-group {
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}
.main-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
  font-size: 36rpx;
  font-weight: bold;
  background: linear-gradient(135deg, #67c23a, #409eff);
  color: #fff;
  border: none;
  border-radius: 12rpx;
  padding: 32rpx 0;
  cursor: pointer;
  transition: background 0.2s, transform 0.2s;
}
.main-btn:active {
  background: linear-gradient(135deg, #409eff, #67c23a);
  transform: translateY(-2rpx);
}
.icon {
  font-size: 40rpx;
  margin-right: 12rpx;
}
</style> 