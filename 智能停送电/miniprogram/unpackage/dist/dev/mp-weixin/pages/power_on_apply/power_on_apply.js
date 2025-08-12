"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  __name: "power_on_apply",
  setup(__props) {
    const list = common_vendor.ref([]);
    const loading = common_vendor.ref(false);
    const user = common_vendor.index.getStorageSync("user") || {};
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
    const fetchList = async () => {
      loading.value = true;
      try {
        const res = await common_vendor.index.request({
          url: "http://localhost:5050/api/mp/applications",
          method: "GET",
          timeout: 1e4
        });
        list.value = (res.data || []).filter(
          (app) => ["approved", "verified", "repairing", "repair_completed"].includes(app.status) && app.applicant === user.realname
          // 只显示自己的
        );
      } catch (e) {
        common_vendor.index.__f__("error", "at pages/power_on_apply/power_on_apply.vue:60", "获取申请列表失败:", e);
        list.value = [];
      } finally {
        loading.value = false;
      }
    };
    const applyPowerOn = async (id) => {
      common_vendor.index.showLoading({ title: "提交中..." });
      try {
        const res = await common_vendor.index.request({
          url: "http://localhost:5050/api/mp/power-on-apply",
          method: "POST",
          header: { "Content-Type": "application/json" },
          data: { id },
          timeout: 1e4
        });
        if (res.statusCode === 200) {
          common_vendor.index.showToast({ title: "送电申请已提交", icon: "success" });
          fetchList();
        } else {
          common_vendor.index.showToast({ title: res.data.msg || "提交失败", icon: "none" });
        }
      } catch (err) {
        common_vendor.index.__f__("error", "at pages/power_on_apply/power_on_apply.vue:83", "提交送电申请失败:", err);
        common_vendor.index.showToast({ title: "网络错误", icon: "none" });
      } finally {
        common_vendor.index.hideLoading();
      }
    };
    common_vendor.onMounted(fetchList);
    return (_ctx, _cache) => {
      return common_vendor.e({
        a: loading.value
      }, loading.value ? {} : common_vendor.e({
        b: list.value.length === 0
      }, list.value.length === 0 ? {} : {
        c: common_vendor.f(list.value, (item, k0, i0) => {
          return {
            a: common_vendor.t(item.deviceId),
            b: common_vendor.t(item.reason),
            c: common_vendor.t(item.applicant),
            d: common_vendor.t(formatDateTime(item.created_at)),
            e: common_vendor.t(item.status === "power_on_applied" ? "已申请送电" : "申请送电"),
            f: common_vendor.o(($event) => applyPowerOn(item.id), item.id),
            g: item.status === "power_on_applied",
            h: item.id
          };
        })
      }));
    };
  }
};
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["__scopeId", "data-v-1bf1cf0f"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/power_on_apply/power_on_apply.js.map
