<template>
  <view class="login-wrapper">
    <view class="login-box">
      <view class="login-title">
        ⚡ 智能停送电系统登录
      </view>

      <view class="form-group">
        <input class="input" v-model="form.username" placeholder="用户名" />
      </view>

      <view class="form-group">
        <input class="input" v-model="form.password" type="password" placeholder="密码" />
      </view>

      <button class="login-button" @click="login">登录</button>
      
      <view class="divider">
        <text class="divider-text">或</text>
      </view>
      
      <button class="register-button" @click="goToRegister">
        <text class="register-icon">👤</text>
        <text>注册新用户</text>
      </button>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      form: {
        username: '',
        password: ''
      }
    };
  },
  methods: {
    login() {
      const { username, password } = this.form;
      if (!username || !password) {
        uni.showToast({ title: '请填写用户名和密码', icon: 'none' });
        return;
      }

      uni.request({
        url: 'http://localhost:5050/api/login',
        method: 'POST',
        header: { 'Content-Type': 'application/json' },
        data: this.form,
        success: (res) => {
          if (res.statusCode === 200) {
            uni.setStorageSync('user', res.data);
            // 单独保存用户角色，方便权限检查
            if (res.data && res.data.role) {
              uni.setStorageSync('user_role', res.data.role);
              console.log('保存用户角色:', res.data.role);
            }
            // 登录成功后
            if (res.data && res.data.role) {
              const role = res.data.role;
              if (role === 'electrician') {
                uni.reLaunch({ url: '/pages/electrician_home/electrician_home' });
              } else if (role === 'dispatcher') {
                uni.reLaunch({ url: '/pages/dispatcher_home/dispatcher_home' });
              } else if (role === 'admin') {
                uni.reLaunch({ url: '/pages/admin/admin' });
              } else {
                uni.reLaunch({ url: '/pages/index/index' }); // 普通用户或默认
              }
            }
          } else {
            uni.showToast({ title: res.data.msg || '登录失败', icon: 'error' });
          }
        },
        fail: () => {
          uni.showToast({ title: '网络错误', icon: 'error' });
        }
      });
    },
    
    goToRegister() {
      uni.navigateTo({
        url: '/pages/register/register'
      });
    }
  }
};
</script>

<style>
.login-wrapper {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(to bottom right, #1e3c72, #2a5298);
}

.login-box {
  width: 600rpx;
  background-color: #0e1a2b;
  padding: 60rpx 40rpx;
  border-radius: 20rpx;
  box-shadow: 0 0 30rpx rgba(0, 0, 0, 0.3);
}

.login-title {
  text-align: center;
  font-size: 36rpx;
  font-weight: bold;
  color: #49a6ff;
  margin-bottom: 40rpx;
}

.form-group {
  margin-bottom: 30rpx;
}

.input {
  width: 100%;
  height: 80rpx; 
  padding: 0 24rpx;
  font-size: 30rpx;
  line-height: 80rpx; 
  color: #fff;
  background: #1c2b3e;
  border: none;
  border-radius: 12rpx;
  box-sizing: border-box;
}

.input::placeholder {
  color: #aaa;
  font-size: 28rpx;
}

.login-button {
  width: 100%;
  background: linear-gradient(to right, #3ca1ff, #007bff);
  color: white;
  font-size: 32rpx; 
  padding: 24rpx;   
  border: none;
  border-radius: 10rpx;
  margin-bottom: 30rpx;
}

.divider {
  position: relative;
  text-align: center;
  margin: 30rpx 0;
}

.divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1rpx;
  background: #2a3f5f;
}

.divider-text {
  background: #0e1a2b;
  padding: 0 20rpx;
  color: #666;
  font-size: 24rpx;
}

.register-button {
  width: 100%;
  background: rgba(255, 255, 255, 0.1);
  color: #49a6ff;
  font-size: 28rpx;
  padding: 20rpx;
  border: 2rpx solid #49a6ff;
  border-radius: 10rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
}

.register-icon {
  font-size: 24rpx;
}
</style>
