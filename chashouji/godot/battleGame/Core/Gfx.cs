using Godot;

namespace Chashouji {

/* 一层能每帧重建的 2D 几何。就是一个 Node2D 加两个属性 —— CanvasItem
   本来就是干这个的，不需要自己拼网格和材质。 */
public partial class MeshLayer : Node2D {
    public readonly Draw2D D = new Draw2D();

    public override void _Draw() { D.Flush(GetCanvasItem()); }

    /// 重建完调一次。Godot 的 _Draw 不是每帧自动跑的，不调就是画面冻住而逻辑在跑
    public void Commit() => QueueRedraw();
}

public static class Gfx {
    /* 混合模式。对**纯顶点色**几何，内置的两个模式就与网页画布逐像素等价：
         Mix = SrcAlpha/OneMinusSrcAlpha → src.rgb*a + dst*(1-a)   = source-over
         Add = SrcAlpha/One             → src.rgb*a + dst          = lighter
       所以不写自定义 shader —— 少一个"运行时才按名字取、打包后静默失效"
       的东西。 */
    static CanvasItemMaterial mix, add;

    public static CanvasItemMaterial MixMat =>
        mix ??= new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Mix };

    /// 相加（对应网页版的 globalCompositeOperation = 'lighter'）
    public static CanvasItemMaterial AddMat =>
        add ??= new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add };

    /* 画面层次全靠 ZIndex 定。Godot 的 ZIndex 取值范围是 ±4096，而且是**同一
       个 CanvasLayer 内**的排序，跨层要用 CanvasLayer.layer —— 这套画面全在
       一层里，用 ZIndex 就够。 */
    public static MeshLayer NewLayer(Node parent, string name, bool additive, int z) {
        var n = new MeshLayer { Name = name, ZIndex = z, Material = additive ? AddMat : MixMat };
        parent.AddChild(n);
        return n;
    }

    /// 给已有的 CanvasItem 挂混合模式与层序，贴图层用
    public static T Setup<T>(this T n, Node parent, string name, bool additive, int z)
            where T : CanvasItem {
        n.Name = name; n.ZIndex = z;
        n.Material = additive ? AddMat : MixMat;
        parent.AddChild(n);
        return n;
    }
}
}
