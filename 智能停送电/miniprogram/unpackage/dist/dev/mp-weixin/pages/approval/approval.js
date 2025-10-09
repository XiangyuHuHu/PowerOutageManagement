"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  data() {
    return {
      loading: true,
      applications: [],
      stats: {
        pending: 0,
        approved: 0,
        rejected: 0
      },
      statusOptions: ["全部状态", "待审批", "已审批", "已驳回", "送电申请"],
      typeOptions: ["全部类型", "停电申请", "送电申请"],
      selectedStatus: "",
      selectedType: ""
    };
  },
  computed: {
    filteredApplications() {
      let filtered = this.applications;
      if (this.selectedStatus && this.selectedStatus !== "全部状态") {
        const statusMap = {
          "待审批": "pending",
          "已审批": "approved",
          "已驳回": "rejected",
          "送电申请": "power_on_applied"
        };
        filtered = filtered.filter((app) => app.status === statusMap[this.selectedStatus]);
      }
      if (this.selectedType && this.selectedType !== "全部类型") {
        const typeMap = {
          "停电申请": "power_off",
          "送电申请": "power_on"
        };
        filtered = filtered.filter((app) => app.type === typeMap[this.selectedType]);
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
      const user = common_vendor.index.getStorageSync("user");
      if (!user || user.role !== "admin" && user.role !== "dispatcher") {
        common_vendor.index.showToast({
          title: "权限不足",
          icon: "none"
        });
        common_vendor.index.navigateBack();
      }
    },
    async fetchApplications() {
      this.loading = true;
      try {
        const response = await common_vendor.index.request({
          url: "http://localhost:5050/api/mp/applications",
          method: "GET",
          timeout: 1e4
        });
        if (response.statusCode === 200) {
          this.applications = response.data;
          this.updateStats();
        } else {
          common_vendor.index.showToast({
            title: "获取申请列表失败",
            icon: "none"
          });
        }
      } catch (err) {
        common_vendor.index.__f__("error", "at pages/approval/approval.vue:210", "获取申请列表失败:", err);
        common_vendor.index.showToast({
          title: "网络错误",
          icon: "none"
        });
      } finally {
        this.loading = false;
      }
    },
    updateStats() {
      this.stats.pending = this.applications.filter((app) => app.status === "pending").length;
      this.stats.approved = this.applications.filter((app) => app.status === "approved").length;
      this.stats.rejected = this.applications.filter((app) => ["rejected", "power_on_rejected"].includes(app.status)).length;
    },
    getStatusText(status) {
      const statusMap = {
        "pending": "待审批",
        "approved": "已审批",
        "rejected": "已驳回",
        "verified": "已验电",
        "repairing": "检修中",
        "repair_completed": "检修完成",
        "power_on_applied": "送电申请",
        "completed": "已完成",
        "power_on_rejected": "送电驳回"
      };
      return statusMap[status] || status;
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
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit"
      });
    },
    onStatusChange(e) {
      this.selectedStatus = this.statusOptions[e.detail.value];
    },
    onTypeChange(e) {
      this.selectedType = this.typeOptions[e.detail.value];
    },
    viewDetail(id) {
      common_vendor.index.navigateTo({
        url: `/pages/approval/detail?id=${id}`
      });
    },
    async approveApplication(id) {
      common_vendor.index.showModal({
        title: "确认审批",
        content: "确定通过这个申请吗？",
        success: async (res) => {
          if (res.confirm) {
            try {
              const response = await common_vendor.index.request({
                url: "http://localhost:5050/api/mp/approve-application",
                method: "POST",
                header: { "Content-Type": "application/json" },
                data: { id },
                timeout: 1e4
              });
              if (response.statusCode === 200) {
                common_vendor.index.showToast({
                  title: "审批通过成功",
                  icon: "success"
                });
                this.fetchApplications();
              } else {
                common_vendor.index.showToast({
                  title: response.data.msg || "审批失败",
                  icon: "none"
                });
              }
            } catch (err) {
              common_vendor.index.__f__("error", "at pages/approval/approval.vue:309", "审批失败:", err);
              common_vendor.index.showToast({
                title: "网络错误",
                icon: "none"
              });
            }
          }
        }
      });
    },
    async rejectApplication(id) {
      common_vendor.index.showModal({
        title: "确认驳回",
        content: "确定驳回这个申请吗？",
        success: async (res) => {
          if (res.confirm) {
            try {
              const response = await common_vendor.index.request({
                url: "http://localhost:5050/api/mp/reject-application",
                method: "POST",
                header: { "Content-Type": "application/json" },
                data: { id },
                timeout: 1e4
              });
              if (response.statusCode === 200) {
                common_vendor.index.showToast({
                  title: "驳回成功",
                  icon: "success"
                });
                this.fetchApplications();
              } else {
                common_vendor.index.showToast({
                  title: response.data.msg || "驳回失败",
                  icon: "none"
                });
              }
            } catch (err) {
              common_vendor.index.__f__("error", "at pages/approval/approval.vue:348", "驳回失败:", err);
              common_vendor.index.showToast({
                title: "网络错误",
                icon: "none"
              });
            }
          }
        }
      });
    },
    async approvePowerOn(id) {
      common_vendor.index.showModal({
        title: "确认送电",
        content: "确定同意送电吗？",
        success: async (res) => {
          if (res.confirm) {
            try {
              const response = await common_vendor.index.request({
                url: "http://localhost:5050/api/mp/approve-power-on",
                method: "POST",
                header: { "Content-Type": "application/json" },
                data: { id },
                timeout: 1e4
              });
              if (response.statusCode === 200) {
                common_vendor.index.showToast({
                  title: "送电审批通过",
                  icon: "success"
                });
                this.fetchApplications();
              } else {
                common_vendor.index.showToast({
                  title: response.data.msg || "审批失败",
                  icon: "none"
                });
              }
            } catch (err) {
              common_vendor.index.__f__("error", "at pages/approval/approval.vue:387", "送电审批失败:", err);
              common_vendor.index.showToast({
                title: "网络错误",
                icon: "none"
              });
            }
          }
        }
      });
    },
    async rejectPowerOn(id) {
      common_vendor.index.showModal({
        title: "确认拒绝",
        content: "确定拒绝送电吗？",
        success: async (res) => {
          if (res.confirm) {
            try {
              const response = await common_vendor.index.request({
                url: "http://localhost:5050/api/mp/reject-power-on",
                method: "POST",
                header: { "Content-Type": "application/json" },
                data: { id },
                timeout: 1e4
              });
              if (response.statusCode === 200) {
                common_vendor.index.showToast({
                  title: "送电申请已拒绝",
                  icon: "success"
                });
                this.fetchApplications();
              } else {
                common_vendor.index.showToast({
                  title: response.data.msg || "操作失败",
                  icon: "none"
                });
              }
            } catch (err) {
              common_vendor.index.__f__("error", "at pages/approval/approval.vue:426", "拒绝送电失败:", err);
              common_vendor.index.showToast({
                title: "网络错误",
                icon: "none"
              });
            }
          }
        }
      });
    },
    goBack() {
      common_vendor.index.navigateBack();
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: common_vendor.t($data.stats.pending),
    b: common_vendor.t($data.stats.approved),
    c: common_vendor.t($data.stats.rejected),
    d: common_vendor.t($data.selectedStatus || "全部状态"),
    e: $data.statusOptions,
    f: common_vendor.o((...args) => $options.onStatusChange && $options.onStatusChange(...args)),
    g: common_vendor.t($data.selectedType || "全部类型"),
    h: $data.typeOptions,
    i: common_vendor.o((...args) => $options.onTypeChange && $options.onTypeChange(...args)),
    j: $data.loading
  }, $data.loading ? {} : $options.filteredApplications.length === 0 ? {} : {
    l: common_vendor.f($options.filteredApplications, (app, k0, i0) => {
      return common_vendor.e({
        a: common_vendor.t(app.id),
        b: common_vendor.t($options.getStatusText(app.status)),
        c: common_vendor.n("status-" + app.status),
        d: common_vendor.t(app.applicant_name || app.applicant),
        e: common_vendor.t(app.device_id),
        f: common_vendor.t(app.reason),
        g: common_vendor.t($options.formatDateTime(app.created_at)),
        h: app.status === "pending"
      }, app.status === "pending" ? {
        i: common_vendor.o(($event) => $options.approveApplication(app.id), app.id)
      } : {}, {
        j: app.status === "pending"
      }, app.status === "pending" ? {
        k: common_vendor.o(($event) => $options.rejectApplication(app.id), app.id)
      } : {}, {
        l: app.status === "power_on_applied"
      }, app.status === "power_on_applied" ? {
        m: common_vendor.o(($event) => $options.approvePowerOn(app.id), app.id)
      } : {}, {
        n: app.status === "power_on_applied"
      }, app.status === "power_on_applied" ? {
        o: common_vendor.o(($event) => $options.rejectPowerOn(app.id), app.id)
      } : {}, {
        p: app.id,
        q: common_vendor.o(($event) => $options.viewDetail(app.id), app.id)
      });
    })
  }, {
    k: $options.filteredApplications.length === 0,
    m: common_vendor.o((...args) => $options.goBack && $options.goBack(...args))
  });
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/approval/approval.js.map
