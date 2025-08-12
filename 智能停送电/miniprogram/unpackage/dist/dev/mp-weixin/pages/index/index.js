"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  methods: {
    doFaceVerify() {
      common_vendor.index.showModal({
        title: "人脸识别成功",
        content: "您已通过身份验证，前往填写申请单",
        success: (res) => {
          if (res.confirm) {
            common_vendor.index.navigateTo({
              url: "/pages/apply/apply"
            });
          }
        }
      });
    },
    goToVerify() {
      common_vendor.index.navigateTo({ url: "/pages/poweroff/verify?id=1" });
    },
    goToRepair() {
      common_vendor.index.navigateTo({ url: "/pages/poweroff/repair?id=1" });
    },
    goToRestore() {
      common_vendor.index.navigateTo({ url: "/pages/poweroff/restore?id=1" });
    },
    selectRole(role) {
      if (role === "electrician") {
        common_vendor.index.navigateTo({ url: "/pages/poweroff/verify?id=1" });
      } else if (role === "dispatcher") {
        common_vendor.index.navigateTo({ url: "/pages/test/test" });
      }
    },
    simulateScan() {
      common_vendor.index.showToast({ title: "扫码成功，进入验电页", icon: "success" });
      setTimeout(() => {
        common_vendor.index.navigateTo({ url: "/pages/poweroff/verify?id=1" });
      }, 1e3);
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return {
    a: common_vendor.o((...args) => $options.doFaceVerify && $options.doFaceVerify(...args)),
    b: common_vendor.o((...args) => $options.goToVerify && $options.goToVerify(...args)),
    c: common_vendor.o((...args) => $options.goToRepair && $options.goToRepair(...args)),
    d: common_vendor.o((...args) => $options.goToRestore && $options.goToRestore(...args)),
    e: common_vendor.o(($event) => $options.selectRole("electrician")),
    f: common_vendor.o(($event) => $options.selectRole("dispatcher")),
    g: common_vendor.o((...args) => $options.simulateScan && $options.simulateScan(...args))
  };
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/index/index.js.map
