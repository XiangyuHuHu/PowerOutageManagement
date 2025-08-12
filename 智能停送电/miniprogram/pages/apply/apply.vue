<template>
  <view class="apply-page">
    <view class="form-box">
      <view class="form-title">⚡ 停电申请表</view>

      <view class="form-item">
        <text class="label">申请人</text>
        <input v-model="form.applicant" class="input" placeholder="请输入姓名" />
      </view>

      <view class="form-item">
        <text class="label">停电时间</text>
        <uni-datetime-picker type="datetime" v-model="form.date" class="input" />
      </view>

      <view class="form-item">
        <text class="label">设备编号</text>
        <picker :range="deviceOptions" @change="onDeviceChange">
          <view class="input">{{ form.deviceId || '请选择设备编号' }}</view>
        </picker>
      </view>

      <view class="form-item">
        <text class="label">停电原因</text>
        <picker :range="reasonOptions" @change="onReasonChange">
          <view class="input">{{ form.reason || '请选择停电原因' }}</view>
        </picker>
      </view>

      <button class="submit-btn" @click="submitForm">提交申请</button>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      form: {
        applicant: '',
        date: '',
        deviceId: '',
        reason: ''
      },
      deviceOptions: ['配电柜A1', '配电柜A2', '配电柜B1'],
      reasonOptions: ['线路检修', '设备维护', '其他']
    };
  },
  onLoad() {
    const user = uni.getStorageSync('user');
    if (user && user.realname) {
      this.form.applicant = user.realname;
    } else if (user && user.username) {
      this.form.applicant = user.username;
    }
  },
  methods: {
    onDeviceChange(e) {
      this.form.deviceId = this.deviceOptions[e.detail.value];
    },
    onReasonChange(e) {
      this.form.reason = this.reasonOptions[e.detail.value];
    },
    submitForm() {
      const { applicant, date, deviceId, reason } = this.form;
      if (!applicant || !date || !deviceId || !reason) {
        uni.showToast({ title: '请填写完整', icon: 'none' });
        return;
      }

      uni.request({
        url: 'http://localhost:5050/api/mp/power-apply',
        method: 'POST',
        header: { 'Content-Type': 'application/json' },
        data: this.form,
        timeout: 10000,
        success: (res) => {
          if (res.statusCode === 200) {
            uni.showToast({ title: '提交成功', icon: 'success' });
            setTimeout(() => uni.navigateBack(), 1500);
          } else {
            uni.showToast({ title: res.data.msg || '提交失败', icon: 'error' });
          }
        },
        fail: () => {
          uni.showToast({ title: '网络错误', icon: 'error' });
        }
      });
    }
  }
};
</script>


<style>
.apply-page {
  background: linear-gradient(145deg, #2a3b4c, #1e2a39);
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
.form-box {
  background-color: #101d2c;
  padding: 60rpx;
  border-radius: 20rpx;
  width: 650rpx;
  box-shadow: 0 8rpx 20rpx rgba(0, 0, 0, 0.2);
}
.form-title {
  text-align: center;
  color: #4fc3f7;
  font-size: 38rpx;
  font-weight: bold;
  margin-bottom: 40rpx;
}
.form-item {
  margin-bottom: 40rpx;
}
.label {
  display: block;
  color: #ffffff;
  margin-bottom: 12rpx;
  font-size: 28rpx;
}
.input {
  background-color: #1c2b3e;
  color: #ffffff;
  padding: 20rpx;
  border-radius: 12rpx;
  font-size: 28rpx;
}
.submit-btn {
  background: linear-gradient(to right, #4fc3f7, #2196f3);
  color: white;
  padding: 20rpx;
  font-size: 30rpx;
  border: none;
  border-radius: 12rpx;
  width: 100%;
}
</style>
