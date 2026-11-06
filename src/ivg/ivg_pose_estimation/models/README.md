# rembg u2net 权重

`u2net.onnx` 约 168MB，超过 Gitee 社区版单文件配额与 GitHub 100MB，**不随 git 入库**。运行时 `U2NET_HOME` 指向本目录；本机已有该文件则保留。

clone 后若本目录没有 `u2net.onnx`：

```bash
./fetch_u2net.sh
```

也可在首次抠图时由 rembg/pooch 自动下载（需能访问 GitHub）。官方地址与 rembg `v0.0.0` 发布物一致：

https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx

## MobileSAM 本地副本

当前采摘模型路径为 `src/peach/peach_scene_perception/model/mobile_sam.pt`。`fetch_mobile_sam.sh` 仍先探测已退役的 `peach_harvester/model/` 路径，当前不存在时会尝试下载；本次文档整理没有改变该脚本行为。若需要离线恢复，可在本目录显式复制当前仓内权重：

```bash
cp ../../../peach/peach_scene_perception/model/mobile_sam.pt ./mobile_sam.pt
```

该目录下的权重仍按 `.gitignore` 仅留本机；来源与许可遵循模型原说明。
