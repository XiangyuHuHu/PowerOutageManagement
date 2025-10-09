"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  __name: "electrician_home",
  setup(__props) {
    const goApply = () => {
      common_vendor.index.navigateTo({ url: "/pages/apply/apply" });
    };
    const goPowerOnApply = () => {
      common_vendor.index.navigateTo({ url: "/pages/power_on_apply/power_on_apply" });
    };
    const goRepair = () => {
      common_vendor.index.navigateTo({ url: "/pages/poweroff/repair" });
    };
    const goHistory = () => {
      common_vendor.index.navigateTo({ url: "/pages/approval/history" });
    };
    return (_ctx, _cache) => {
      return {
        a: common_vendor.o(goApply),
        b: common_vendor.o(goPowerOnApply),
        c: common_vendor.o(goRepair),
        d: common_vendor.o(goHistory)
      };
    };
  }
};
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["__scopeId", "data-v-d151ccf5"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/electrician_home/electrician_home.js.map
