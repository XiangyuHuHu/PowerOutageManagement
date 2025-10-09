"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  data() {
    return {
      info: {
        id: 0,
        applicant: "",
        date: "",
        deviceId: "",
        reason: "",
        status: ""
      }
    };
  },
  methods: {
    async submitRestore() {
      const res = await common_vendor.index.request({
        url: "http://localhost:5050/api/update-status",
        method: "POST",
        data: {
          id: this.info.id,
          status: "restored"
        }
      });
      if (res[1].statusCode === 200) {
        common_vendor.index.showToast({ title: "送电完成", icon: "success" });
        this.info.status = "restored";
      } else {
        common_vendor.index.showToast({ title: "提交失败", icon: "none" });
      }
    }
  },
  onLoad(options) {
    const id = options.id;
    common_vendor.index.request({
      url: `http://localhost:5050/api/get?id=${id}`,
      success: (res) => {
        const data = res.data;
        if (data.status !== "restore-allowed") {
          common_vendor.index.showToast({ title: "当前状态不允许送电", icon: "none" });
          setTimeout(() => common_vendor.index.navigateBack(), 1500);
        } else {
          this.info = data;
        }
      }
    });
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return {
    a: common_vendor.t($data.info.applicant),
    b: common_vendor.t($data.info.date),
    c: common_vendor.t($data.info.deviceId),
    d: common_vendor.t($data.info.reason),
    e: common_vendor.t($data.info.status),
    f: common_vendor.o((...args) => $options.submitRestore && $options.submitRestore(...args))
  };
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/poweroff/restore.js.map
