<template>
  <view class="main">
    <view class="title"><text class="icon">🔧</text> 电工工作台</view>
    <view class="btn-group">
      <button class="main-btn" @click="goApply">
        <text class="icon">📝</text> 停电申请
      </button>
      <button class="main-btn" @click="goPowerOnApply">
        <text class="icon">🔌</text> 送电申请
      </button>
      <button class="main-btn" @click="goRepair">
        <text class="icon">🛠️</text> 检修/我的申请
      </button>
      <button class="main-btn" @click="goHistory">
        <text class="icon">📜</text> 历史记录
      </button>
    </view>
  </view>
</template>

<script setup>
const goApply = () => {
  uni.navigateTo({ url: '/pages/apply/apply' });
};
const goPowerOnApply = () => {
  uni.navigateTo({ url: '/pages/power_on_apply/power_on_apply' });
};
const goRepair = () => {
  uni.navigateTo({ url: '/pages/poweroff/repair' });
};
const goHistory = () => {
  uni.navigateTo({ url: '/pages/approval/history' });
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
  background: linear-gradient(135deg, #409eff, #2a6bc5);
  color: #fff;
  border: none;
  border-radius: 12rpx;
  padding: 32rpx 0;
  cursor: pointer;
  transition: background 0.2s, transform 0.2s;
}
.main-btn:active {
  background: linear-gradient(135deg, #2a6bc5, #409eff);
  transform: translateY(-2rpx);
}
.icon {
  font-size: 40rpx;
  margin-right: 12rpx;
}
</style> 