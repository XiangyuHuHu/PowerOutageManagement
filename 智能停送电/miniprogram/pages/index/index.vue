<template>
  <view class="container">
    <button type="primary" @click="doFaceVerify">点击进行人脸识别</button>

    <view class="section-title">调试入口</view>

    <button type="default" @click="goToVerify">跳转到验电页面</button>
    <button type="default" @click="goToRepair">跳转到检修页面</button>
    <button type="default" @click="goToRestore">跳转到送电页面</button>

    <view class="section-title">角色入口</view>

    <button @click="selectRole('electrician')">我是电工</button>
    <button @click="selectRole('dispatcher')">我是调度员</button>

    <view class="section-title">扫码模拟</view>

    <button type="warn" @click="simulateScan">模拟扫码跳转（验电）</button>
  </view>
</template>

<script>
export default {
  methods: {
    doFaceVerify() {
      uni.showModal({
        title: '人脸识别成功',
        content: '您已通过身份验证，前往填写申请单',
        success: res => {
          if (res.confirm) {
            uni.navigateTo({
              url: '/pages/apply/apply'
            });
          }
        }
      });
    },
    goToVerify() {
      uni.navigateTo({ url: '/pages/poweroff/verify?id=1' });
    },
    goToRepair() {
      uni.navigateTo({ url: '/pages/poweroff/repair?id=1' });
    },
    goToRestore() {
      uni.navigateTo({ url: '/pages/poweroff/restore?id=1' });
    },
    selectRole(role) {
      if (role === 'electrician') {
        uni.navigateTo({ url: '/pages/poweroff/verify?id=1' });
      } else if (role === 'dispatcher') {
        uni.navigateTo({ url: '/pages/test/test' }); // 示例跳转，可自定义为审批后台
      }
    },
    simulateScan() {
      uni.showToast({ title: '扫码成功，进入验电页', icon: 'success' });
      setTimeout(() => {
        uni.navigateTo({ url: '/pages/poweroff/verify?id=1' });
      }, 1000);
    }
  }
}
</script>

<style>
.container {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: center;
  height: 100vh;
  padding: 30rpx;
}
button {
  width: 80%;
  margin-bottom: 20rpx;
}
.section-title {
  margin: 30rpx 0 10rpx;
  font-weight: bold;
  font-size: 28rpx;
}
</style>
