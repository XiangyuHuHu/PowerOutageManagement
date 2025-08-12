<template>
  <view class="approval-container">
    <view class="header">
      <view class="header-content">
        <view class="logo-icon">
          <text class="icon">📋</text>
        </view>
        <view class="header-text">
          <text class="title">审批管理</text>
          <text class="subtitle">智能停送电系统 - 调度审批后台</text>
        </view>
      </view>
    </view>
    
    <view class="stats-container">
      <view class="stat-item">
        <text class="stat-number">{{ stats.pending }}</text>
        <text class="stat-label">待审批</text>
      </view>
      <view class="stat-item">
        <text class="stat-number">{{ stats.approved }}</text>
        <text class="stat-label">已审批</text>
      </view>
      <view class="stat-item">
        <text class="stat-number">{{ stats.rejected }}</text>
        <text class="stat-label">已驳回</text>
      </view>
    </view>
    
    <view class="content">
      <view class="filter-section">
        <view class="filter-item">
          <text class="filter-label">状态筛选：</text>
          <picker :range="statusOptions" @change="onStatusChange">
            <view class="picker">{{ selectedStatus || '全部状态' }}</view>
          </picker>
        </view>
        <view class="filter-item">
          <text class="filter-label">类型筛选：</text>
          <picker :range="typeOptions" @change="onTypeChange">
            <view class="picker">{{ selectedType || '全部类型' }}</view>
          </picker>
        </view>
      </view>
      
      <view v-if="loading" class="loading">
        <text>加载中...</text>
      </view>
      
      <view v-else-if="filteredApplications.length === 0" class="empty">
        <text>暂无申请记录</text>
      </view>
      
      <view v-else class="application-list">
        <view 
          v-for="app in filteredApplications" 
          :key="app.id" 
          class="application-item"
          @click="viewDetail(app.id)"
        >
          <view class="app-header">
            <text class="app-id">#{{ app.id }}</text>
            <view class="status-tag" :class="'status-' + app.status">
              <text>{{ getStatusText(app.status) }}</text>
            </view>
          </view>
          
          <view class="app-content">
            <view class="app-row">
              <text class="label">申请人：</text>
              <text class="value">{{ app.applicant_name || app.applicant }}</text>
            </view>
            <view class="app-row">
              <text class="label">设备编号：</text>
              <text class="value">{{ app.device_id }}</text>
            </view>
            <view class="app-row">
              <text class="label">申请原因：</text>
              <text class="value">{{ app.reason }}</text>
            </view>
            <view class="app-row">
              <text class="label">申请时间：</text>
              <text class="value">{{ formatDateTime(app.created_at) }}</text>
            </view>
          </view>
          
          <view class="app-actions">
            <button 
              v-if="app.status === 'pending'" 
              class="action-btn approve-btn"
              @click.stop="approveApplication(app.id)"
            >
              审批通过
            </button>
            <button 
              v-if="app.status === 'pending'" 
              class="action-btn reject-btn"
              @click.stop="rejectApplication(app.id)"
            >
              驳回申请
            </button>
            <button 
              v-if="app.status === 'power_on_applied'" 
              class="action-btn approve-btn"
              @click.stop="approvePowerOn(app.id)"
            >
              同意送电
            </button>
            <button 
              v-if="app.status === 'power_on_applied'" 
              class="action-btn reject-btn"
              @click.stop="rejectPowerOn(app.id)"
            >
              拒绝送电
            </button>
          </view>
        </view>
      </view>
    </view>
    
    <view class="footer">
      <button class="back-btn" @click="goBack">
        <text class="icon">←</text>
        <text>返回</text>
      </button>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      loading: true,
      applications: [],
      stats: {
        pending: 0,
        approved: 0,
        rejected: 0
      },
      statusOptions: ['全部状态', '待审批', '已审批', '已驳回', '送电申请'],
      typeOptions: ['全部类型', '停电申请', '送电申请'],
      selectedStatus: '',
      selectedType: ''
    };
  },
  
  computed: {
    filteredApplications() {
      let filtered = this.applications;
      
      if (this.selectedStatus && this.selectedStatus !== '全部状态') {
        const statusMap = {
          '待审批': 'pending',
          '已审批': 'approved',
          '已驳回': 'rejected',
          '送电申请': 'power_on_applied'
        };
        filtered = filtered.filter(app => app.status === statusMap[this.selectedStatus]);
      }
      
      if (this.selectedType && this.selectedType !== '全部类型') {
        const typeMap = {
          '停电申请': 'power_off',
          '送电申请': 'power_on'
        };
        filtered = filtered.filter(app => app.type === typeMap[this.selectedType]);
      }
      
      return filtered;
    }
  },
  
  onLoad() {
    this.checkPermission();
    this.fetchApplications();
  },
  
  methods: {
    checkPermission() {
      const user = uni.getStorageSync('user');
      if (!user || (user.role !== 'admin' && user.role !== 'dispatcher')) {
        uni.showToast({
          title: '权限不足',
          icon: 'none'
        });
        uni.navigateBack();
      }
    },
    
    async fetchApplications() {
      this.loading = true;
      try {
        const response = await uni.request({
          url: 'http://localhost:5050/api/mp/applications',
          method: 'GET',
          timeout: 10000
        });
        
        if (response.statusCode === 200) {
          this.applications = response.data;
          this.updateStats();
        } else {
          uni.showToast({
            title: '获取申请列表失败',
            icon: 'none'
          });
        }
      } catch (err) {
        console.error('获取申请列表失败:', err);
        uni.showToast({
          title: '网络错误',
          icon: 'none'
        });
      } finally {
        this.loading = false;
      }
    },
    
    updateStats() {
      this.stats.pending = this.applications.filter(app => app.status === 'pending').length;
      this.stats.approved = this.applications.filter(app => app.status === 'approved').length;
      this.stats.rejected = this.applications.filter(app => ['rejected', 'power_on_rejected'].includes(app.status)).length;
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
    
    onStatusChange(e) {
      this.selectedStatus = this.statusOptions[e.detail.value];
    },
    
    onTypeChange(e) {
      this.selectedType = this.typeOptions[e.detail.value];
    },
    
    viewDetail(id) {
      uni.navigateTo({
        url: `/pages/approval/detail?id=${id}`
      });
    },
    
    async approveApplication(id) {
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
                data: { id },
                timeout: 10000
              });
              
              if (response.statusCode === 200) {
                uni.showToast({
                  title: '审批通过成功',
                  icon: 'success'
                });
                this.fetchApplications();
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
    
    async rejectApplication(id) {
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
                data: { id },
                timeout: 10000
              });
              
              if (response.statusCode === 200) {
                uni.showToast({
                  title: '驳回成功',
                  icon: 'success'
                });
                this.fetchApplications();
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
    
    async approvePowerOn(id) {
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
                data: { id },
                timeout: 10000
              });
              
              if (response.statusCode === 200) {
                uni.showToast({
                  title: '送电审批通过',
                  icon: 'success'
                });
                this.fetchApplications();
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
    
    async rejectPowerOn(id) {
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
                data: { id },
                timeout: 10000
              });
              
              if (response.statusCode === 200) {
                uni.showToast({
                  title: '送电申请已拒绝',
                  icon: 'success'
                });
                this.fetchApplications();
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
.approval-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
  color: #fff;
}

.header {
  background: linear-gradient(to right, #0c1d2c, #1a3a5f);
  padding: 40rpx;
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

.stats-container {
  display: flex;
  gap: 30rpx;
  background: rgba(0, 30, 60, 0.5);
  padding: 30rpx 40rpx;
  margin: 20rpx;
  border-radius: 12rpx;
  border: 1rpx solid rgba(64, 158, 255, 0.3);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.stat-number {
  font-size: 48rpx;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 8rpx;
}

.stat-label {
  font-size: 24rpx;
  color: #a0d9ff;
}

.content {
  padding: 20rpx;
}

.filter-section {
  display: flex;
  gap: 20rpx;
  margin-bottom: 30rpx;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.filter-label {
  font-size: 26rpx;
  color: #a0d9ff;
}

.picker {
  background: rgba(255, 255, 255, 0.1);
  padding: 15rpx 20rpx;
  border-radius: 8rpx;
  border: 1rpx solid rgba(64, 158, 255, 0.3);
  font-size: 26rpx;
  color: #fff;
  min-width: 200rpx;
}

.loading, .empty {
  text-align: center;
  padding: 100rpx 0;
  color: #888;
  font-size: 28rpx;
}

.application-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.application-item {
  background: rgba(12, 28, 44, 0.7);
  border-radius: 12rpx;
  padding: 30rpx;
  border: 1rpx solid rgba(64, 158, 255, 0.2);
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.app-id {
  font-size: 28rpx;
  font-weight: bold;
  color: #409eff;
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

.app-content {
  margin-bottom: 20rpx;
}

.app-row {
  display: flex;
  margin-bottom: 10rpx;
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

.app-actions {
  display: flex;
  gap: 15rpx;
}

.action-btn {
  flex: 1;
  padding: 15rpx;
  border: none;
  border-radius: 8rpx;
  font-size: 24rpx;
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

.footer {
  padding: 30rpx;
  display: flex;
  justify-content: center;
}

.back-btn {
  background: linear-gradient(135deg, #409eff, #2a6bc5);
  color: #fff;
  border: none;
  border-radius: 12rpx;
  padding: 20rpx 40rpx;
  font-size: 28rpx;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 10rpx;
}
</style>
