<template>
  <view class="admin-container">
    <view class="header">
      <view class="header-content">
        <view class="logo-icon">
          <text class="icon">👑</text>
        </view>
        <view class="header-text">
          <text class="title">管理员控制台</text>
          <text class="subtitle">智能停送电系统 - 管理员权限</text>
        </view>
      </view>
    </view>
    
    <view class="user-info">
      <text class="info-title">当前用户信息</text>
      <view class="user-details">
        <view class="user-detail">
          <text class="label">用户名：</text>
          <text class="value">{{ userInfo.username || '管理员' }}</text>
        </view>
        <view class="user-detail">
          <text class="label">角色：</text>
          <text class="value">{{ userInfo.role || '管理员' }}</text>
        </view>
        <view class="user-detail">
          <text class="label">权限：</text>
          <text class="value">全部权限</text>
        </view>
      </view>
    </view>
    
    <view class="function-grid">
      <view class="function-card" @click="goToApproval">
        <view class="card-icon approval-icon">
          <text class="icon">📋</text>
        </view>
        <text class="card-title">审批管理</text>
        <text class="card-desc">处理停电送电申请</text>
      </view>
      
      <view class="function-card" @click="goToStats">
        <view class="card-icon stats-icon">
          <text class="icon">📊</text>
        </view>
        <text class="card-title">系统统计</text>
        <text class="card-desc">查看系统数据分析</text>
      </view>
      
      <view class="function-card" @click="goToUserManagement">
        <view class="card-icon user-icon">
          <text class="icon">👥</text>
        </view>
        <text class="card-title">用户管理</text>
        <text class="card-desc">管理系统用户和权限</text>
      </view>
      
      <view class="function-card" @click="goToRepair">
        <view class="card-icon repair-icon">
          <text class="icon">🔧</text>
        </view>
        <text class="card-title">检修管理</text>
        <text class="card-desc">设备检修任务管理</text>
      </view>
      
      <view class="function-card" @click="goToDeviceMonitor">
        <view class="card-icon monitor-icon">
          <text class="icon">📡</text>
        </view>
        <text class="card-title">设备监控</text>
        <text class="card-desc">实时设备状态监控</text>
      </view>
    </view>
    
    <view class="logout-section">
      <button class="logout-btn" @click="logout">
        <text class="logout-icon">🚪</text>
        <text>退出登录</text>
      </button>
    </view>
    
             <!-- 测试按钮 -->
         <view class="test-section">
           <text class="test-title">测试功能</text>
           <button class="test-btn" @click="goToSimpleUserManagement">
             测试简化版用户管理
           </button>
           <button class="test-btn" @click="goToLightUserManagement" style="margin-top: 20rpx;">
             测试轻量版用户管理
           </button>
         </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      userInfo: {}
    };
  },
  onLoad() {
    this.checkLogin();
    this.getUserInfo();
  },
  methods: {
    checkLogin() {
      const user = uni.getStorageSync('user');
      if (!user) {
        uni.reLaunch({ url: '/pages/login/login' });
      }
    },
    
    getUserInfo() {
      const user = uni.getStorageSync('user');
      if (user) {
        this.userInfo = user;
      }
    },
    
    goToApproval() {
      uni.showLoading({ title: '加载中...' });
      uni.navigateTo({
        url: '/pages/approval/approval',
        timeout: 5000,
        success: () => {
          uni.hideLoading();
        },
        fail: (err) => {
          uni.hideLoading();
          console.error('跳转到审批页面失败:', err);
          uni.showToast({
            title: '页面跳转失败',
            icon: 'none'
          });
        }
      });
    },
    
    goToStats() {
      uni.showLoading({ title: '加载中...' });
      uni.navigateTo({
        url: '/pages/stats/stats',
        timeout: 5000,
        success: () => {
          uni.hideLoading();
        },
        fail: (err) => {
          uni.hideLoading();
          console.error('跳转到统计页面失败:', err);
          uni.showToast({
            title: '页面跳转失败',
            icon: 'none'
          });
        }
      });
    },
    
    goToUserManagement() {
      uni.showLoading({ title: '加载中...' });
      
      // 先检查页面是否存在
      setTimeout(() => {
        uni.navigateTo({
          url: '/pages/user_management/user_management',
          timeout: 10000, // 增加到10秒
          success: () => {
            uni.hideLoading();
            console.log('用户管理页面跳转成功');
          },
          fail: (err) => {
            uni.hideLoading();
            console.error('跳转到用户管理页面失败:', err);
            
            // 尝试使用switchTab或reLaunch作为备选方案
            if (err.errMsg && err.errMsg.includes('timeout')) {
              uni.showModal({
                title: '页面跳转超时',
                content: '是否尝试重新跳转？',
                success: (res) => {
                  if (res.confirm) {
                    // 尝试使用reLaunch
                    uni.reLaunch({
                      url: '/pages/user_management/user_management',
                      fail: (reLaunchErr) => {
                        console.error('reLaunch也失败了:', reLaunchErr);
                        uni.showToast({
                          title: '页面跳转失败，请检查网络',
                          icon: 'none',
                          duration: 3000
                        });
                      }
                    });
                  }
                }
              });
            } else {
              uni.showToast({
                title: '页面跳转失败',
                icon: 'none',
                duration: 3000
              });
            }
          }
        });
      }, 100); // 延迟100ms再跳转
    },
    
    goToRepair() {
      uni.showLoading({ title: '加载中...' });
      uni.navigateTo({
        url: '/pages/repair/repair',
        timeout: 5000,
        success: () => {
          uni.hideLoading();
        },
        fail: (err) => {
          uni.hideLoading();
          console.error('跳转到检修页面失败:', err);
          uni.showToast({
            title: '页面跳转失败',
            icon: 'none'
          });
        }
      });
    },
    
    logout() {
      uni.showModal({
        title: '确认退出',
        content: '确定要退出登录吗？',
        success: (res) => {
          if (res.confirm) {
            uni.clearStorageSync();
            uni.reLaunch({
              url: '/pages/login/login'
            });
          }
        }
      });
    },
    
    goToSimpleUserManagement() {
      console.log('跳转到简化版用户管理页面');
      uni.showLoading({ title: '加载中...' });
      uni.navigateTo({
        url: '/pages/user_management_simple/user_management_simple',
        timeout: 10000,
        success: () => {
          uni.hideLoading();
          console.log('简化版用户管理页面跳转成功');
        },
        fail: (err) => {
          uni.hideLoading();
          console.error('简化版用户管理页面跳转失败:', err);
          uni.showToast({
            title: '页面跳转失败',
            icon: 'none'
          });
        }
      });
    },
    
    goToLightUserManagement() {
      console.log('跳转到轻量版用户管理页面');
      uni.showLoading({ title: '加载中...' });
      uni.navigateTo({
        url: '/pages/user_management_light/user_management_light',
        timeout: 10000,
        success: () => {
          uni.hideLoading();
          console.log('轻量版用户管理页面跳转成功');
        },
        fail: (err) => {
          uni.hideLoading();
          console.error('轻量版用户管理页面跳转失败:', err);
          uni.showToast({
            title: '页面跳转失败',
            icon: 'none'
          });
        }
      });
    },
    
    goToDeviceMonitor() {
      console.log('跳转到设备监控页面');
      uni.showLoading({ title: '加载中...' });
      uni.navigateTo({
        url: '/pages/device_monitor/device_monitor',
        timeout: 10000,
        success: () => {
          uni.hideLoading();
          console.log('设备监控页面跳转成功');
        },
        fail: (err) => {
          uni.hideLoading();
          console.error('设备监控页面跳转失败:', err);
          uni.showToast({
            title: '页面跳转失败',
            icon: 'none'
          });
        }
      });
    }
  }
};
</script>

<style>
.admin-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 0;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40rpx;
  display: flex;
  justify-content: center;
  align-items: center;
}

.header-content {
  display: flex;
  align-items: center;
}

.logo-icon {
  width: 80rpx;
  height: 80rpx;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
}

.icon {
  font-size: 40rpx;
}

.header-text {
  display: flex;
  flex-direction: column;
}

.title {
  font-size: 36rpx;
  font-weight: bold;
  color: #fff;
}

.subtitle {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 5rpx;
}

.user-info {
  background: #fff;
  margin: 30rpx;
  padding: 30rpx;
  border-radius: 15rpx;
  box-shadow: 0 5rpx 15rpx rgba(0, 0, 0, 0.1);
}

.info-title {
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
  display: block;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 15rpx;
}

.user-detail {
  display: flex;
  align-items: center;
}

.label {
  font-size: 26rpx;
  color: #666;
  min-width: 120rpx;
}

.value {
  font-size: 26rpx;
  color: #333;
  font-weight: 500;
}

.function-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20rpx;
  padding: 0 30rpx;
  margin-bottom: 40rpx;
}

.function-card {
  background: #fff;
  border-radius: 15rpx;
  padding: 30rpx;
  text-align: center;
  box-shadow: 0 5rpx 15rpx rgba(0, 0, 0, 0.1);
  transition: transform 0.2s;
}

.function-card:active {
  transform: scale(0.95);
}

.card-icon {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20rpx;
}

.approval-icon {
  background: linear-gradient(135deg, #409eff, #2a6bc5);
}

.stats-icon {
  background: linear-gradient(135deg, #67c23a, #4a8c2c);
}

.user-icon {
  background: linear-gradient(135deg, #e6a23c, #b88230);
}

.repair-icon {
  background: linear-gradient(135deg, #f56c6c, #c45656);
}

.card-icon .icon {
  font-size: 36rpx;
  color: #fff;
}

.card-title {
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 10rpx;
  display: block;
}

.card-desc {
  font-size: 22rpx;
  color: #666;
  display: block;
}

.logout-section {
  padding: 0 30rpx;
}

.logout-btn {
  width: 100%;
  background: linear-gradient(135deg, #f56c6c, #c45656);
  color: #fff;
  border: none;
  border-radius: 15rpx;
  padding: 25rpx;
  font-size: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
}

.logout-icon {
  font-size: 24rpx;
}

/* 响应式设计 */
@media (max-width: 750rpx) {
  .function-grid {
    grid-template-columns: 1fr;
  }
  
  .header {
    padding: 30rpx 20rpx;
  }
  
  .user-info {
    margin: 20rpx;
    padding: 25rpx;
  }
}

.test-section {
  margin-top: 40rpx;
  padding: 30rpx;
  background: #f8f9fa;
  border-radius: 15rpx;
}

.test-title {
  display: block;
  font-size: 28rpx;
  color: #666;
  margin-bottom: 20rpx;
  text-align: center;
}

.test-btn {
  background: #28a745;
  color: white;
  border: none;
  border-radius: 10rpx;
  padding: 20rpx;
  font-size: 26rpx;
  width: 100%;
}
</style>
