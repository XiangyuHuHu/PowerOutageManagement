<template>
  <view class="container">
    <view class="title">测试跳转页面</view>

    <button type="primary" @click="goto('verify')">跳转到电工验电</button>
    <button type="primary" @click="goto('repair')">跳转到电工检修</button>
    <button type="primary" @click="goto('restore')">跳转到电工送电</button>
  </view>
</template>

<script>
export default {
  methods: {
    goto(type) {
      uni.navigateTo({
        url: `/pages/poweroff/${type}?id=1`
      });
    }
  }
}
</script>

<style>
.container {
  padding: 40rpx;
}
.title {
  font-size: 36rpx;
  margin-bottom: 30rpx;
}
button {
  margin-bottom: 20rpx;
}
</style>
