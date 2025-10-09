"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  data() {
    return {
      loading: true,
      stats: {
        totalApplications: 0,
        approvedApplications: 0,
        pendingApplications: 0,
        rejectedApplications: 0,
        newApplications: 0,
        approvalRate: 0,
        totalUsers: 0,
        activeUsers: 0,
        adminUsers: 0,
        dispatcherUsers: 0,
        electricianUsers: 0
      },
      recentActivities: []
    };
  },
  onLoad() {
    this.checkPermission();
    this.fetchStats();
  },
  methods: {
    checkPermission() {
      const userRole = common_vendor.index.getStorageSync("user_role");
      if (userRole !== "admin") {
        common_vendor.index.showToast({
          title: "只有管理员可以访问统计页面",
          icon: "none"
        });
        common_vendor.index.navigateBack();
      }
    },
    formatDateTime(timestamp) {
      if (!timestamp)
        return "";
      let dateStr = timestamp;
      if (typeof timestamp === "string") {
        dateStr = timestamp.replace(/-/g, "/");
      }
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) {
        return timestamp;
      }
      return date.toLocaleString("zh-CN", {
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit"
      });
    },
    getActivityColor(type) {
      const colors = {
        "apply": "linear-gradient(135deg, #409eff, #2a6bc5)",
        "approve": "linear-gradient(135deg, #67c23a, #4a8c2c)",
        "reject": "linear-gradient(135deg, #f56c6c, #c45656)",
        "user": "linear-gradient(135deg, #e6a23c, #b88230)"
      };
      return colors[type] || colors["apply"];
    },
    getActivityIcon(type) {
      const icons = {
        "apply": "📝",
        "approve": "✅",
        "reject": "❌",
        "user": "👤"
      };
      return icons[type] || "📋";
    },
    async fetchStats() {
      try {
        const statsRes = await common_vendor.index.request({
          url: "http://localhost:5050/api/mp/stats",
          method: "GET",
          header: {
            "Content-Type": "application/json"
          },
          timeout: 1e4
          // 10秒超时
        });
        const applicationsRes = await common_vendor.index.request({
          url: "http://localhost:5050/api/mp/applications",
          method: "GET",
          header: {
            "Content-Type": "application/json"
          },
          timeout: 1e4
          // 10秒超时
        });
        if (statsRes.statusCode === 200 && applicationsRes.statusCode === 200) {
          const stats = statsRes.data;
          const applications = applicationsRes.data;
          this.stats.totalApplications = stats.applications;
          this.stats.totalUsers = stats.users;
          this.stats.approvedApplications = applications.filter((app) => app.status === "approved").length;
          this.stats.pendingApplications = applications.filter((app) => app.status === "pending").length;
          this.stats.rejectedApplications = applications.filter((app) => app.status === "rejected").length;
          const totalProcessed = this.stats.approvedApplications + this.stats.rejectedApplications;
          this.stats.approvalRate = totalProcessed > 0 ? Math.round(this.stats.approvedApplications / totalProcessed * 100) : 0;
          const today = /* @__PURE__ */ new Date();
          const todayApplications = applications.filter((app) => {
            const appDate = new Date(app.created_at);
            return appDate.toDateString() === today.toDateString();
          });
          this.stats.newApplications = todayApplications.length;
          this.stats.adminUsers = stats.role_stats.admin || 0;
          this.stats.dispatcherUsers = stats.role_stats.dispatcher || 0;
          this.stats.electricianUsers = stats.role_stats.electrician || 0;
          this.stats.activeUsers = stats.users;
          this.recentActivities = applications.slice(0, 5).map((app) => ({
            id: app.id,
            type: app.status === "approved" ? "approve" : app.status === "rejected" ? "reject" : "apply",
            title: `${app.applicant_name || "未知用户"} 提交了${app.type === "power_off" ? "停电" : "送电"}申请`,
            time: app.created_at
          }));
        } else {
          common_vendor.index.showToast({
            title: "获取统计数据失败",
            icon: "none"
          });
        }
      } catch (err) {
        common_vendor.index.__f__("error", "at pages/stats/stats.vue:304", "获取统计数据失败：", err);
        common_vendor.index.showToast({
          title: "网络错误",
          icon: "none"
        });
      } finally {
        this.loading = false;
      }
    },
    goBack() {
      common_vendor.index.navigateBack();
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: common_vendor.o((...args) => $options.goBack && $options.goBack(...args)),
    b: $data.loading
  }, $data.loading ? {} : common_vendor.e({
    c: common_vendor.t($data.stats.totalApplications),
    d: common_vendor.t($data.stats.newApplications),
    e: common_vendor.t($data.stats.approvedApplications),
    f: common_vendor.t($data.stats.approvalRate),
    g: common_vendor.t($data.stats.pendingApplications),
    h: common_vendor.t($data.stats.totalUsers),
    i: common_vendor.t($data.stats.activeUsers),
    j: common_vendor.t($data.stats.approvedApplications),
    k: common_vendor.t($data.stats.pendingApplications),
    l: common_vendor.t($data.stats.rejectedApplications),
    m: common_vendor.t($data.stats.adminUsers),
    n: common_vendor.t($data.stats.dispatcherUsers),
    o: common_vendor.t($data.stats.electricianUsers),
    p: $data.recentActivities.length === 0
  }, $data.recentActivities.length === 0 ? {} : {
    q: common_vendor.f($data.recentActivities, (activity, k0, i0) => {
      return {
        a: common_vendor.t($options.getActivityIcon(activity.type)),
        b: $options.getActivityColor(activity.type),
        c: common_vendor.t(activity.title),
        d: common_vendor.t($options.formatDateTime(activity.time)),
        e: activity.id
      };
    })
  }));
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-3598459f"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/stats/stats.js.map
