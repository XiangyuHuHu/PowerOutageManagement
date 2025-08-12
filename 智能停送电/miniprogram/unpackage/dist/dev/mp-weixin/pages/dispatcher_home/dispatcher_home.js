"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  __name: "dispatcher_home",
  setup(__props) {
    const goApproval = () => {
      common_vendor.index.navigateTo({ url: "/pages/approval/approval" });
    };
    const goHistory = () => {
      common_vendor.index.navigateTo({ url: "/pages/approval/history" });
    };
    const goStats = () => {
      common_vendor.index.showToast({ title: "敬请期待", icon: "none" });
    };
    return (_ctx, _cache) => {
      return {
        a: common_vendor.o(goApproval),
        b: common_vendor.o(goHistory),
        c: common_vendor.o(goStats)
      };
    };
  }
};
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["__scopeId", "data-v-62500fc0"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/dispatcher_home/dispatcher_home.js.map
