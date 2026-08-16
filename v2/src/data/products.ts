export type Product = {
  slug: string;
  maker: string;
  name: string;
  category: string;
  lead: string;
  facts: string[];
  uses: string[];
  system: string[];
  officialNote: string;
};

export const products: Product[] = [
  {
    slug: 'unitree-g1-d', maker: 'Unitree', name: 'G1-D', category: '研究開発向けヒューマノイド',
    lead: '遠隔操作・データ収集から模倣学習・VLA、実機評価までをつなぐ研究開発プラットフォーム。',
    facts: ['Flagship 19 DoF', '垂直作業空間 0–2 m', '遠隔操作遅延 <100 ms', 'データ収集 60 Hz'],
    uses: ['模倣学習', 'VLA・マルチモーダル研究', '移動操作', 'ロボットデータ収集・評価'],
    system: ['ロボット本体', '遠隔操作', 'データ収集', 'データセット', '学習・推論', '実機評価・再収集'],
    officialNote: '主要仕様はUnitree公式情報・正式資料を確認。',
  },
  {
    slug: 'unitree-g1', maker: 'Unitree', name: 'G1', category: 'ヒューマノイドロボット',
    lead: '全身運動、操作研究、模倣学習・強化学習に展開できる研究・教育向けヒューマノイド。',
    facts: ['全身23〜43自由度の構成', '約132 cm', '約35 kg', '研究・教育向け開発構成あり'],
    uses: ['全身運動研究', '操作・力制御', '模倣学習', '強化学習・教育'],
    system: ['本体・末端', '深度カメラ・LiDAR', 'SDK・制御', 'GPU・学習', '実機評価'],
    officialNote: '構成により仕様が異なるため、最終仕様はUnitree公式情報で確認。',
  },
  {
    slug: 'unitree-go2', maker: 'Unitree', name: 'Go2', category: '四足歩行ロボット',
    lead: '移動・地形認識・マッピング・巡回・センシング研究に展開できる四足歩行プラットフォーム。',
    facts: ['4D LiDAR L2', '重量約15 kg', 'X/EDU 最大速度約5 m/s', 'EDU 二次開発対応'],
    uses: ['巡回・点検', 'SLAM・マッピング', 'センシング', '屋内外PoC'],
    system: ['Go2', 'LiDAR・深度カメラ', 'SDK・ROS 2', 'マッピング・認識', 'ログ・評価'],
    officialNote: 'モデル・構成ごとの差異はUnitree公式情報で確認。',
  },
  {
    slug: 'agibot-x2-edu', maker: 'AGIBOT', name: 'X2 EDU', category: '教育・実習向けヒューマノイド',
    lead: '組立・調整・運動制御からROS 2二次開発までを実機で学ぶ教育・実習プラットフォーム。',
    facts: ['29自由度', 'RK3588', 'ROS 2 SDK / DDS', 'MuJoCo簡易シミュレーション'],
    uses: ['ロボット組立実習', '運動制御', 'ROS 2開発', 'PBL・研究入門'],
    system: ['組立・調整', '運動制御', 'ROS 2 / DDS', 'シミュレーション', 'PBL・実機評価'],
    officialNote: '主要仕様・実習内容はAGIBOT正式教育資料を確認。',
  },
  {
    slug: 'agibot-x2-rec', maker: 'AGIBOT', name: 'X2 REC', category: 'データ収集向けヒューマノイド',
    lead: '全身遠隔操作とデータ取得を核に、学習・検証までをつなぐロボットデータ収集プラットフォーム。',
    facts: ['全身遠隔操作', 'Data Acquisition 2.0', 'マルチセンサー構成', 'Genie Studio連携'],
    uses: ['ロボットデータ収集', '模倣学習', 'VLA', '実機評価・再学習'],
    system: ['X2 REC', '遠隔操作', 'データ取得', 'データ処理', '学習', '検証・再収集'],
    officialNote: '主要仕様はAGIBOT 2026正式製品資料を確認。',
  },
  {
    slug: 'agibot-g2', maker: 'AGIBOT', name: 'G2', category: '精密操作・産業PoC向け',
    lead: '高精度フォースコントロールと実環境での安定運用を重視した汎用エンボディドAIロボット。',
    facts: ['産業グレード設計', 'IP42', '高精度フォースコントロール', '精密操作・学習展開'],
    uses: ['精密操作', '把持・搬送', '具身AI研究', '産業PoC'],
    system: ['G2', 'センサー・末端', '力制御', '学習・制御', 'PoC評価'],
    officialNote: '公式仕様・対応構成はAGIBOT公式情報を確認。',
  },
  {
    slug: 'agibot-a3', maker: 'AGIBOT', name: 'A3', category: 'サービス・教育向けフルサイズヒューマノイド',
    lead: '長時間稼働、対人インタラクション、位置決め、複数台運用に強みを持つフルサイズヒューマノイド。',
    facts: ['約173 cm', '約55 kg', '31自由度', '最大10時間の長時間運用構成'],
    uses: ['案内・教育', '展示・サービス', 'HRI', '複数台運用'],
    system: ['A3', '対話・認識', '位置決め', '運用システム', '複数台管理'],
    officialNote: '主要仕様はAGIBOT A3公式製品資料・マニュアルを確認。',
  },
  {
    slug: 'agibot-a2-ultra', maker: 'AGIBOT', name: 'A2 Ultra', category: 'フルサイズヒューマノイド',
    lead: '全身機構、認識、対話、自律移動を備え、研究から案内・サービスまで展開できるフルサイズヒューマノイド。',
    facts: ['40自由度', '約169 cm', '約69 kg', '3D LiDAR / RGB-D / 高演算力モジュール'],
    uses: ['ロボット研究', '案内・対話', '自律移動', 'デモ・サービスPoC'],
    system: ['A2 Ultra', '認識・対話', '自律移動', '開発環境', 'PoC・運用'],
    officialNote: '主要仕様はAGIBOT A2 Ultra公式日本語製品情報を確認。',
  },
];
