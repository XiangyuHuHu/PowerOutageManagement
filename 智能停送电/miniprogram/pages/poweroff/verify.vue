<template>
  <view class="container">
    <view class="title">电工验电流程</view>

    <view class="card">
      <text>申请人：{{ info.applicant }}</text>
      <text>时间：{{ info.date }}</text>
      <text>设备编号：{{ info.deviceId }}</text>
      <text>停电原因：{{ info.reason }}</text>
      <text>当前状态：{{ info.status }}</text>
    </view>

    <button type="primary" @click="verifyPower">验电完成</button>
  </view>
</template>

<script>
export default {
  data() {
    return {
      info: {}
    };
  },
  methods: {
    verifyPower() {
      uni.request({
        url: 'http://localhost:5050/api/update-status',
        method: 'POST',
        data: {
          id: this.info.id,
          status: 'verified'
        },
        success: (res) => {
          if (res.statusCode === 200) {
            uni.showToast({ title: '验电完成', icon: 'success' });
            this.info.status = 'verified';
          } else {
            uni.showToast({ title: '提交失败', icon: 'none' });
          }
        },
        fail: () => {
          uni.showToast({ title: '网络错误', icon: 'none' });
        }
      });
    }
  },
  onLoad(options) {
    const id = options.id;
    uni.request({
      url: `http://localhost:5050/api/get?id=${id}`,
      success: (res) => {
        this.info = res.data;
        if (this.info.status !== 'approved') {
          uni.showToast({ title: '当前状态不允许验电', icon: 'none' });
          setTimeout(() => uni.navigateBack(), 1500);
        }
      }
    });
  }
};
</script>

<style>
.container {
  padding: 20rpx;
}
.title {
  font-size: 36rpx;
  font-weight: bold;
  margin-bottom: 30rpx;
}
.card {
  border: 1px solid #ccc;
  border-radius: 10rpx;
  padding: 20rpx;
  margin-bottom: 40rpx;
}
.card text {
  display: block;
  margin-bottom: 15rpx;
}
</style>