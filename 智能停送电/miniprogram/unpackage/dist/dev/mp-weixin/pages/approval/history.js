"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  __name: "history",
  setup(__props) {
    const historyList = common_vendor.ref([]);
    const loading = common_vendor.ref(false);
    const user = common_vendor.index.getStorageSync("user") || {};
    const statusMap = {
      pending: "待审批",
      approved: "审批通过",
      rejected: "审批驳回",
      verified: "已验电",
      "verify-rejected": "验电驳回",
      repairing: "检修中",
      repair_completed: "检修完成",
      power_on_applied: "送电申请",
      completed: "已完成",
      power_on_rejected: "送电驳回"
    };
    const statusText = (status) => statusMap[status] || status;
    const formatDateTime = (timestamp) => {
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
    };
    const fetchHistory = async () => {
      loading.value = true;
      try {
        const res = await common_vendor.index.request({
          url: `http://localhost:5050/api/mp/my-applications?applicant=${encodeURIComponent(user.realname || user.username)}`,
          method: "GET",
          timeout: 1e4
        });
        historyList.value = (res.data || []).filter((app) => !["pending", "power_on_applied"].includes(app.status));
      } catch (err) {
        common_vendor.index.__f__("error", "at pages/approval/history.vue:84", "获取历史记录失败:", err);
        historyList.value = [];
      } finally {
        loading.value = false;
      }
    };
    const viewDetail = (id) => {
      common_vendor.index.navigateTo({ url: `/pages/approval/detail?id=${id}` });
    };
    common_vendor.onMounted(() => {
      fetchHistory();
    });
    return (_ctx, _cache) => {
      return common_vendor.e({
        a: loading.value
      }, loading.value ? {} : common_vendor.e({
        b: historyList.value.length === 0
      }, historyList.value.length === 0 ? {} : {
        c: common_vendor.f(historyList.value, (item, k0, i0) => {
          return {
            a: common_vendor.t(item.applicant),
            b: common_vendor.t(item.device_id),
            c: common_vendor.t(item.reason),
            d: common_vendor.t(formatDateTime(item.created_at)),
            e: common_vendor.t(statusText(item.status)),
            f: item.id,
            g: common_vendor.o(($event) => viewDetail(item.id), item.id)
          };
        })
      }));
    };
  }
};
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["__scopeId", "data-v-9748df46"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/approval/history.js.map
