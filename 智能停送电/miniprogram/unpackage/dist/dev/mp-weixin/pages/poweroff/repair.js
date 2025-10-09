"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  __name: "repair",
  setup(__props) {
    const list = common_vendor.ref([]);
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
      return date.toLocaleString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
    };
    const fetchList = async () => {
      loading.value = true;
      try {
        const res = await common_vendor.index.request({ url: "http://localhost:5050/api/list", method: "GET", withCredentials: true });
        list.value = (res.data.data || res.data).filter((app) => app.applicant === user.realname);
      } catch (e) {
        list.value = [];
      } finally {
        loading.value = false;
      }
    };
    const canRepair = (item) => ["repairing"].includes(item.status);
    const doRepair = async (id) => {
      common_vendor.index.showLoading({ title: "提交中..." });
      try {
        const res = await common_vendor.index.request({
          url: "http://localhost:5050/api/update-status",
          method: "POST",
          data: { id, status: "repair_completed" },
          withCredentials: true
        });
        if (res[1].statusCode === 200) {
          common_vendor.index.showToast({ title: "检修完成", icon: "success" });
          fetchList();
        } else {
          common_vendor.index.showToast({ title: res[1].data.msg || "提交失败", icon: "none" });
        }
      } finally {
        common_vendor.index.hideLoading();
      }
    };
    const viewDetail = (id) => {
      common_vendor.index.navigateTo({ url: `/pages/approval/detail?id=${id}` });
    };
    common_vendor.onMounted(fetchList);
    return (_ctx, _cache) => {
      return common_vendor.e({
        a: loading.value
      }, loading.value ? {} : common_vendor.e({
        b: list.value.length === 0
      }, list.value.length === 0 ? {} : {
        c: common_vendor.f(list.value, (item, k0, i0) => {
          return common_vendor.e({
            a: common_vendor.t(item.deviceId),
            b: common_vendor.t(item.reason),
            c: common_vendor.t(formatDateTime(item.created_at)),
            d: common_vendor.t(statusText(item.status)),
            e: canRepair(item)
          }, canRepair(item) ? {
            f: common_vendor.o(($event) => doRepair(item.id), item.id)
          } : {}, {
            g: item.id,
            h: common_vendor.o(($event) => viewDetail(item.id), item.id)
          });
        })
      }));
    };
  }
};
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["__scopeId", "data-v-8fc68c79"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/poweroff/repair.js.map
