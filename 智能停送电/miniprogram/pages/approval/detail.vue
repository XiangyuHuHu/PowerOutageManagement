<template>
  <view class="detail-container">
    <view class="header">
      <view class="header-content">
        <view class="logo-icon">
          <text class="icon">📄</text>
        </view>
        <view class="header-text">
          <text class="title">申请详情</text>
          <text class="subtitle">智能停送电系统 - 申请详情查看</text>
        </view>
      </view>
      <button class="back-btn" @click="goBack">
        <text class="icon">←</text>
        <text>返回</text>
      </button>
    </view>
    
    <view v-if="loading" class="loading">
      <text>加载中...</text>
    </view>
    
    <view v-else-if="!application" class="empty">
      <text>申请不存在</text>
    </view>
    
    <view v-else class="content">
      <!-- 基本信息 -->
      <view class="detail-section">
        <view class="section-title">
          <text class="icon">📋</text>
          <text>基本信息</text>
        </view>
        <view class="info-grid">
          <view class="info-item">
            <text class="label">申请ID：</text>
            <text class="value">#{{ application.id }}</text>
          </view>
          <view class="info-item">
            <text class="label">申请人：</text>
            <text class="value">{{ application.applicant_name || application.applicant }}</text>
          </view>
          <view class="info-item">
            <text class="label">申请类型：</text>
            <text class="value">{{ getTypeText(application.type) }}</text>
          </view>
          <view class="info-item">
            <text class="label">当前状态：</text>
            <view class="status-tag" :class="'status-' + application.status">
              <text>{{ getStatusText(application.status) }}</text>
            </view>
          </view>
          <view class="info-item">
            <text class="label">申请时间：</text>
            <text class="value">{{ formatDateTime(application.created_at) }}</text>
          </view>
          <view class="info-item">
            <text class="label">设备编号：</text>
            <text class="value">{{ application.device_id }}</text>
          </view>
        </view>
      </view>
      
      <!-- 申请详情 -->
      <view class="detail-section">
        <view class="section-title">
          <text class="icon">📝</text>
          <text>申请详情</text>
        </view>
        <view class="detail-content">
          <view class="detail-row">
            <text class="label">停电原因：</text>
            <text class="value">{{ application.reason }}</text>
          </view>
          <view class="detail-row" v-if="application.power_off_time">
            <text class="label">停电时间：</text>
            <text class="value">{{ formatDateTime(application.power_off_time) }}</text>
          </view>
          <view class="detail-row" v-if="application.location">
            <text class="label">设备位置：</text>
            <text class="value">{{ application.location }}</text>
          </view>
          <view class="detail-row" v-if="application.description">
            <text class="label">详细说明：</text>
            <text class="value">{{ application.description }}</text>
          </view>
        </view>
      </view>
      
      <!-- 审批记录 -->
      <view class="detail-section" v-if="application.approval_history && application.approval_history.length > 0">
        <view class="section-title">
          <text class="icon">📊</text>
          <text>审批记录</text>
        </view>
        <view class="history-list">
          <view 
            v-for="(record, index) in application.approval_history" 
            :key="index"
            class="history-item"
          >
            <view class="history-header">
              <text class="history-time">{{ formatDateTime(record.time) }}</text>
              <view class="history-status" :class="'status-' + record.status">
                <text>{{ getStatusText(record.status) }}</text>
              </view>
            </view>
            <view class="history-content">
              <text class="history-operator">操作人：{{ record.operator }}</text>
              <text class="history-comment" v-if="record.comment">备注：{{ record.comment }}</text>
            </view>
          </view>
        </view>
      </view>
      
      <!-- 操作按钮 -->
      <view class="action-section" v-if="canOperate">
        <view class="section-title">
          <text class="icon">⚡</text>
          <text>操作</text>
        </view>
        <view class="action-buttons">
          <button 
            v-if="application.status === 'pending'" 
            class="action-btn approve-btn"
            @click="approveApplication"
          >
            审批通过
          </button>
          <button 
            v-if="application.status === 'pending'" 
            class="action-btn reject-btn"
            @click="rejectApplication"
          >
            驳回申请
          </button>
          <button 
            v-if="application.status === 'power_on_applied'" 
            class="action-btn approve-btn"
            @click="approvePowerOn"
          >
            同意送电
          </button>
          <button 
            v-if="application.status === 'power_on_applied'" 
            class="action-btn reject-btn"
            @click="rejectPowerOn"
          >
            拒绝送电
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      loading: true,
      application: null,
      applicationId: null
    };
  },
  
  computed: {
    canOperate() {
      if (!this.application) return false;
      const user = uni.getStorageSync('user');
      if (!user) return false;
      
      // 管理员和调度员可以操作
      if (user.role === 'admin' || user.role === 'dispatcher') {
        return ['pending', 'power_on_applied'].includes(this.application.status);
      }
      
      return false;
    }
  },
  
  onLoad(options) {
    this.applicationId = options.id;
    this.fetchApplicationDetail();
  },
  
  methods: {
    async fetchApplicationDetail() {
      this.loading = true;
      try {
        const response = await uni.request({
          url: `http://localhost:5050/api/mp/application-detail?id=${this.applicationId}`,
          method: 'GET',
          timeout: 10000
        });
        
        if (response.statusCode === 200) {
          this.application = response.data;
        } else {
          uni.showToast({
            title: '获取申请详情失败',
            icon: 'none'
          });
        }
      } catch (err) {
        console.error('获取申请详情失败:', err);
        uni.showToast({
          title: '网络错误',
          icon: 'none'
        });
      } finally {
        this.loading = false;
      }
    },
    
    getTypeText(type) {
      const typeMap = {
        'power_off': '停电申请',
        'power_on': '送电申请'
      };
      return typeMap[type] || type;
    },
    
    getStatusText(status) {
      const statusMap = {
        'pending': '待审批',
        'approved': '已审批',
        'rejected': '已驳回',
        'verified': '已验电',
        'repairing': '检修中',
        'repair_completed': '检修完成',
        'power_on_applied': '送电申请',
        'completed': '已完成',
        'power_on_rejected': '送电驳回'
      };
      return statusMap[status] || status;
    },
    
    formatDateTime(timestamp) {
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
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    },
    
    async approveApplication() {
      uni.showModal({
        title: '确认审批',
        content: '确定通过这个申请吗？',
        success: async (res) => {
          if (res.confirm) {
            try {
              const response = await uni.request({
                url: 'http://localhost:5050/api/mp/approve-application',
                method: 'POST',
                header: { 'Content-Type': 'application/json' },
                data: { id: this.applicationId },
                timeout: 10000
              });
              
              if (response.statusCode === 200) {
                uni.showToast({
                  title: '审批通过成功',
                  icon: 'success'
                });
                this.fetchApplicationDetail();
              } else {
                uni.showToast({
                  title: response.data.msg || '审批失败',
                  icon: 'none'
                });
              }
            } catch (err) {
              console.error('审批失败:', err);
              uni.showToast({
                title: '网络错误',
                icon: 'none'
              });
            }
          }
        }
      });
    },
    
    async rejectApplication() {
      uni.showModal({
        title: '确认驳回',
        content: '确定驳回这个申请吗？',
        success: async (res) => {
          if (res.confirm) {
            try {
              const response = await uni.request({
                url: 'http://localhost:5050/api/mp/reject-application',
                method: 'POST',
                header: { 'Content-Type': 'application/json' },
                data: { id: this.applicationId },
                timeout: 10000
              });
              
              if (response.statusCode === 200) {
                uni.showToast({
                  title: '驳回成功',
                  icon: 'success'
                });
                this.fetchApplicationDetail();
              } else {
                uni.showToast({
                  title: response.data.msg || '驳回失败',
                  icon: 'none'
                });
              }
            } catch (err) {
              console.error('驳回失败:', err);
              uni.showToast({
                title: '网络错误',
                icon: 'none'
              });
            }
          }
        }
      });
    },
    
    async approvePowerOn() {
      uni.showModal({
        title: '确认送电',
        content: '确定同意送电吗？',
        success: async (res) => {
          if (res.confirm) {
            try {
              const response = await uni.request({
                url: 'http://localhost:5050/api/mp/approve-power-on',
                method: 'POST',
                header: { 'Content-Type': 'application/json' },
                data: { id: this.applicationId },
                timeout: 10000
              });
              
              if (response.statusCode === 200) {
                uni.showToast({
                  title: '送电审批通过',
                  icon: 'success'
                });
                this.fetchApplicationDetail();
              } else {
                uni.showToast({
                  title: response.data.msg || '审批失败',
                  icon: 'none'
                });
              }
            } catch (err) {
              console.error('送电审批失败:', err);
              uni.showToast({
                title: '网络错误',
                icon: 'none'
              });
            }
          }
        }
      });
    },
    
    async rejectPowerOn() {
      uni.showModal({
        title: '确认拒绝',
        content: '确定拒绝送电吗？',
        success: async (res) => {
          if (res.confirm) {
            try {
              const response = await uni.request({
                url: 'http://localhost:5050/api/mp/reject-power-on',
                method: 'POST',
                header: { 'Content-Type': 'application/json' },
                data: { id: this.applicationId },
                timeout: 10000
              });
              
              if (response.statusCode === 200) {
                uni.showToast({
                  title: '送电申请已拒绝',
                  icon: 'success'
                });
                this.fetchApplicationDetail();
              } else {
                uni.showToast({
                  title: response.data.msg || '操作失败',
                  icon: 'none'
                });
              }
            } catch (err) {
              console.error('拒绝送电失败:', err);
              uni.showToast({
                title: '网络错误',
                icon: 'none'
              });
            }
          }
        }
      });
    },
    
    goBack() {
      uni.navigateBack();
    }
  }
};
</script>

<style>
.detail-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
  color: #fff;
}

.header {
  background: linear-gradient(to right, #0c1d2c, #1a3a5f);
  padding: 40rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 2rpx solid #409eff;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.logo-icon {
  width: 80rpx;
  height: 80rpx;
  background: linear-gradient(135deg, #409eff, #1e3a8a);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 20rpx rgba(64, 158, 255, 0.5);
}

.icon {
  font-size: 40rpx;
  color: #fff;
}

.header-text {
  display: flex;
  flex-direction: column;
}

.title {
  font-size: 36rpx;
  font-weight: bold;
  margin-bottom: 8rpx;
  background: linear-gradient(to right, #409eff, #a0d9ff);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.subtitle {
  font-size: 24rpx;
  color: #a0d9ff;
}

.back-btn {
  background: linear-gradient(135deg, #409eff, #2a6bc5);
  color: #fff;
  border: none;
  border-radius: 12rpx;
  padding: 15rpx 30rpx;
  font-size: 26rpx;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.loading, .empty {
  text-align: center;
  padding: 200rpx 0;
  color: #888;
  font-size: 28rpx;
}

.content {
  padding: 30rpx;
}

.detail-section {
  background: rgba(12, 28, 44, 0.7);
  border-radius: 12rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
  border: 1rpx solid rgba(64, 158, 255, 0.2);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 15rpx;
  margin-bottom: 25rpx;
  font-size: 32rpx;
  font-weight: bold;
  color: #409eff;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20rpx;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.label {
  font-size: 26rpx;
  color: #a0d9ff;
  min-width: 120rpx;
}

.value {
  font-size: 26rpx;
  color: #fff;
  flex: 1;
}

.status-tag {
  padding: 8rpx 16rpx;
  border-radius: 6rpx;
  font-size: 22rpx;
  font-weight: bold;
}

.status-pending {
  background: linear-gradient(135deg, #e6a23c, #b88230);
  color: #fff;
}

.status-approved {
  background: linear-gradient(135deg, #409eff, #2a6bc5);
  color: #fff;
}

.status-rejected, .status-power_on_rejected {
  background: linear-gradient(135deg, #f56c6c, #c45656);
  color: #fff;
}

.status-power_on_applied {
  background: linear-gradient(135deg, #67c23a, #4a8c2c);
  color: #fff;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 15rpx;
}

.detail-row {
  display: flex;
  gap: 10rpx;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 15rpx;
}

.history-item {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8rpx;
  padding: 20rpx;
  border: 1rpx solid rgba(64, 158, 255, 0.1);
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10rpx;
}

.history-time {
  font-size: 24rpx;
  color: #a0d9ff;
}

.history-status {
  padding: 6rpx 12rpx;
  border-radius: 4rpx;
  font-size: 20rpx;
  font-weight: bold;
}

.history-content {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.history-operator {
  font-size: 24rpx;
  color: #fff;
}

.history-comment {
  font-size: 22rpx;
  color: #a0d9ff;
}

.action-section {
  background: rgba(12, 28, 44, 0.7);
  border-radius: 12rpx;
  padding: 30rpx;
  border: 1rpx solid rgba(64, 158, 255, 0.2);
}

.action-buttons {
  display: flex;
  gap: 20rpx;
  flex-wrap: wrap;
}

.action-btn {
  flex: 1;
  min-width: 200rpx;
  padding: 20rpx;
  border: none;
  border-radius: 8rpx;
  font-size: 26rpx;
  font-weight: bold;
  cursor: pointer;
}

.approve-btn {
  background: linear-gradient(135deg, #67c23a, #4a8c2c);
  color: #fff;
}

.reject-btn {
  background: linear-gradient(135deg, #f56c6c, #c45656);
  color: #fff;
}
</style> 