"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  data() {
    return {
      loading: true,
      application: null,
      applicationId: null
    };
  },
  computed: {
    canOperate() {
      if (!this.application)
        return false;
      const user = common_vendor.index.getStorageSync("user");
      if (!user)
        return false;
      if (user.role === "admin" || user.role === "dispatcher") {
        return ["pending", "power_on_applied"].includes(this.application.status);
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
        const response = await common_vendor.index.request({
          url: `http://localhost:5050/api/mp/application-detail?id=${this.applicationId}`,
          method: "GET",
          timeout: 1e4
        });
        if (response.statusCode === 200) {
          this.application = response.data;
        } else {
          common_vendor.index.showToast({
            title: "获取申请详情失败",
            icon: "none"
          });
        }
      } catch (err) {
        common_vendor.index.__f__("error", "at pages/approval/detail.vue:206", "获取申请详情失败:", err);
        common_vendor.index.showToast({
          title: "网络错误",
          icon: "none"
        });
      } finally {
        this.loading = false;
      }
    },
    getTypeText(type) {
      const typeMap = {
        "power_off": "停电申请",
        "power_on": "送电申请"
      };
      return typeMap[type] || type;
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
    async approveApplication() {
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
                data: { id: this.applicationId },
                timeout: 1e4
              });
              if (response.statusCode === 200) {
                common_vendor.index.showToast({
                  title: "审批通过成功",
                  icon: "success"
                });
                this.fetchApplicationDetail();
              } else {
                common_vendor.index.showToast({
                  title: response.data.msg || "审批失败",
                  icon: "none"
                });
              }
            } catch (err) {
              common_vendor.index.__f__("error", "at pages/approval/detail.vue:293", "审批失败:", err);
              common_vendor.index.showToast({
                title: "网络错误",
                icon: "none"
              });
            }
          }
        }
      });
    },
    async rejectApplication() {
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
                data: { id: this.applicationId },
                timeout: 1e4
              });
              if (response.statusCode === 200) {
                common_vendor.index.showToast({
                  title: "驳回成功",
                  icon: "success"
                });
                this.fetchApplicationDetail();
              } else {
                common_vendor.index.showToast({
                  title: response.data.msg || "驳回失败",
                  icon: "none"
                });
              }
            } catch (err) {
              common_vendor.index.__f__("error", "at pages/approval/detail.vue:332", "驳回失败:", err);
              common_vendor.index.showToast({
                title: "网络错误",
                icon: "none"
              });
            }
          }
        }
      });
    },
    async approvePowerOn() {
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
                data: { id: this.applicationId },
                timeout: 1e4
              });
              if (response.statusCode === 200) {
                common_vendor.index.showToast({
                  title: "送电审批通过",
                  icon: "success"
                });
                this.fetchApplicationDetail();
              } else {
                common_vendor.index.showToast({
                  title: response.data.msg || "审批失败",
                  icon: "none"
                });
              }
            } catch (err) {
              common_vendor.index.__f__("error", "at pages/approval/detail.vue:371", "送电审批失败:", err);
              common_vendor.index.showToast({
                title: "网络错误",
                icon: "none"
              });
            }
          }
        }
      });
    },
    async rejectPowerOn() {
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
                data: { id: this.applicationId },
                timeout: 1e4
              });
              if (response.statusCode === 200) {
                common_vendor.index.showToast({
                  title: "送电申请已拒绝",
                  icon: "success"
                });
                this.fetchApplicationDetail();
              } else {
                common_vendor.index.showToast({
                  title: response.data.msg || "操作失败",
                  icon: "none"
                });
              }
            } catch (err) {
              common_vendor.index.__f__("error", "at pages/approval/detail.vue:410", "拒绝送电失败:", err);
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
    a: common_vendor.o((...args) => $options.goBack && $options.goBack(...args)),
    b: $data.loading
  }, $data.loading ? {} : !$data.application ? {} : common_vendor.e({
    d: common_vendor.t($data.application.id),
    e: common_vendor.t($data.application.applicant_name || $data.application.applicant),
    f: common_vendor.t($options.getTypeText($data.application.type)),
    g: common_vendor.t($options.getStatusText($data.application.status)),
    h: common_vendor.n("status-" + $data.application.status),
    i: common_vendor.t($options.formatDateTime($data.application.created_at)),
    j: common_vendor.t($data.application.device_id),
    k: common_vendor.t($data.application.reason),
    l: $data.application.power_off_time
  }, $data.application.power_off_time ? {
    m: common_vendor.t($options.formatDateTime($data.application.power_off_time))
  } : {}, {
    n: $data.application.location
  }, $data.application.location ? {
    o: common_vendor.t($data.application.location)
  } : {}, {
    p: $data.application.description
  }, $data.application.description ? {
    q: common_vendor.t($data.application.description)
  } : {}, {
    r: $data.application.approval_history && $data.application.approval_history.length > 0
  }, $data.application.approval_history && $data.application.approval_history.length > 0 ? {
    s: common_vendor.f($data.application.approval_history, (record, index, i0) => {
      return common_vendor.e({
        a: common_vendor.t($options.formatDateTime(record.time)),
        b: common_vendor.t($options.getStatusText(record.status)),
        c: common_vendor.n("status-" + record.status),
        d: common_vendor.t(record.operator),
        e: record.comment
      }, record.comment ? {
        f: common_vendor.t(record.comment)
      } : {}, {
        g: index
      });
    })
  } : {}, {
    t: $options.canOperate
  }, $options.canOperate ? common_vendor.e({
    v: $data.application.status === "pending"
  }, $data.application.status === "pending" ? {
    w: common_vendor.o((...args) => $options.approveApplication && $options.approveApplication(...args))
  } : {}, {
    x: $data.application.status === "pending"
  }, $data.application.status === "pending" ? {
    y: common_vendor.o((...args) => $options.rejectApplication && $options.rejectApplication(...args))
  } : {}, {
    z: $data.application.status === "power_on_applied"
  }, $data.application.status === "power_on_applied" ? {
    A: common_vendor.o((...args) => $options.approvePowerOn && $options.approvePowerOn(...args))
  } : {}, {
    B: $data.application.status === "power_on_applied"
  }, $data.application.status === "power_on_applied" ? {
    C: common_vendor.o((...args) => $options.rejectPowerOn && $options.rejectPowerOn(...args))
  } : {}) : {}), {
    c: !$data.application
  });
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/approval/detail.js.map
