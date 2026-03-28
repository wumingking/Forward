/**
 * Forward 自定义弹幕模块
 * 目标：最大化命中率，尽量最快出弹幕
 */
WidgetMetadata = {
  id: "auto.danmu_api",
  title: "内网弹幕",
  version: "1.0.0",
  requiredVersion: "0.0.2",
  description: "连接内网弹幕服务器接口获取弹幕（极速优化版）",
  author: "zy",
  site: "https://github.com/huangxd-/ForwardWidgets",
  globalParams: [
    {
      name: "server",
      title: "自定义服务器(自部署项目地址：https://github.com/huangxd-/danmu_api.git)",
      type: "input",
      placeholders: [
        {
          title: "示例 danmu_api",
          value: "https://{domain}/{token}",
        },
      ],
    },
  ],
  modules: [
    {
      id: "searchDanmu",
      title: "搜索弹幕",
      functionName: "searchDanmu",
      type: "danmu",
      params: [],
    },
    {
      id: "getDetail",
      title: "获取详情",
      functionName: "getDetailById",
      type: "danmu",
      params: [],
    },
    {
      id: "getComments",
      title: "获取弹幕",
      functionName: "getCommentsById",
      type: "danmu",
      params: [],
    },
  ],
};

function parseData(response) {
  if (!response) throw new Error("获取数据失败");
  return typeof response.data === "string" ? JSON.parse(response.data) : response.data;
}

function normalizeText(text) {
  return String(text || "")
    .toLowerCase()
    .replace(/[【】\[\]（）()<>《》:：·,，.!！?？'"`]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function cleanTitle(text) {
  return String(text || "")
    .replace(/\(.*?\)/g, " ")
    .replace(/（.*?）/g, " ")
    .replace(/\[.*?\]/g, " ")
    .replace(/【.*?】/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function convertChineseNumber(chineseNumber) {
  if (!chineseNumber) return NaN;
  if (/^\d+$/.test(chineseNumber)) return Number(chineseNumber);

  const digits = {
    "零": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "壹": 1,
    "贰": 2,
    "貳": 2,
    "叁": 3,
    "參": 3,
    "肆": 4,
    "伍": 5,
    "陆": 6,
    "陸": 6,
    "柒": 7,
    "捌": 8,
    "玖": 9,
  };

  const units = {
    "十": 10,
    "拾": 10,
    "百": 100,
    "佰": 100,
    "千": 1000,
    "仟": 1000,
  };

  let result = 0;
  let current = 0;

  for (let i = 0; i < chineseNumber.length; i++) {
    const char = chineseNumber[i];
    if (digits[char] !== undefined) {
      current = digits[char];
    } else if (units[char] !== undefined) {
      const unit = units[char];
      if (current === 0) current = 1;
      result += current * unit;
      current = 0;
    }
  }

  result += current;
  return result;
}

function extractSeason(title, queryTitle) {
  const full = cleanTitle(title);
  const query = cleanTitle(queryTitle);

  let tail = full;
  if (full.startsWith(query)) {
    tail = full.slice(query.length).trim();
  }

  let m = tail.match(/第\s*([0-9一二三四五六七八九十零壹贰貳叁參肆伍陆陸柒捌玖拾百佰千仟]+)\s*季/i);
  if (m) return convertChineseNumber(m[1]);

  m = tail.match(/season\s*([0-9]+)/i);
  if (m) return Number(m[1]);

  m = tail.match(/\bs\s*([0-9]+)\b/i);
  if (m) return Number(m[1]);

  m = tail.match(/([0-9]+)(st|nd|rd|th)\s+season/i);
  if (m) return Number(m[1]);

  m = tail.match(/^([0-9]+)\b/);
  if (m) return Number(m[1]);

  m = tail.match(/^([一二三四五六七八九十壹贰貳叁參肆伍陆陸柒捌玖拾]+)/);
  if (m) return convertChineseNumber(m[1]);

  return null;
}

function getTitleScore(animeTitle, queryTitle) {
  const a = normalizeText(cleanTitle(animeTitle));
  const q = normalizeText(cleanTitle(queryTitle));
  if (!a || !q) return 0;

  const aNoSpace = a.replace(/\s+/g, "");
  const qNoSpace = q.replace(/\s+/g, "");

  if (aNoSpace === qNoSpace) return 200;
  if (a === q) return 180;
  if (a.startsWith(q)) return 140;
  if (aNoSpace.startsWith(qNoSpace)) return 130;
  if (a.includes(q)) return 100;
  if (aNoSpace.includes(qNoSpace)) return 90;

  return 0;
}

function getTypeScore(anime, type, queryTitle) {
  const animeType = String(anime.type || "").toLowerCase();
  const q = normalizeText(queryTitle);

  if (type === "movie") {
    if (animeType === "movie") return 80;
    if (q.includes("电影") || q.includes("剧场版") || q.includes("movie")) return 40;
    return 0;
  }

  if (type === "tv") {
    if (animeType === "tvseries" || animeType === "web") return 80;
    return 0;
  }

  return 0;
}

function getSeasonScore(animeTitle, queryTitle, season) {
  if (season === undefined || season === null || season === "") return 0;

  const target = Number(season);
  const found = extractSeason(animeTitle, queryTitle);

  if ((found === null || Number.isNaN(found)) && target === 1) return 40;
  if (Number(found) === target) return 120;
  return 0;
}

function getMovieBonus(animeTitle, type) {
  const t = normalizeText(animeTitle);
  if (type === "movie" && (t.includes("剧场版") || t.includes("movie"))) return 20;
  return 0;
}

function scoreAnime(anime, params) {
  const { title, type, season } = params;
  return (
    getTitleScore(anime.animeTitle || "", title || "") +
    getTypeScore(anime, type, title || "") +
    getSeasonScore(anime.animeTitle || "", title || "", season) +
    getMovieBonus(anime.animeTitle || "", type)
  );
}

async function searchDanmu(params) {
  const { title, server } = params;
  const queryTitle = String(title || "").trim();

  const response = await Widget.http.get(
    `${server}/api/v2/search/anime?keyword=${encodeURIComponent(queryTitle)}`,
    {
      headers: {
        "Content-Type": "application/json",
        "User-Agent": "ForwardWidgets/1.1.0",
      },
    }
  );

  const data = parseData(response);

  if (!data.success) {
    throw new Error(data.errorMessage || "API调用失败");
  }

  let animes = Array.isArray(data.animes) ? data.animes : [];

  animes = animes
    .map((anime) => ({
      ...anime,
      __score: scoreAnime(anime, params),
    }))
    .sort((a, b) => {
      if (b.__score !== a.__score) return b.__score - a.__score;
      return String(a.animeTitle || "").length - String(b.animeTitle || "").length;
    })
    .slice(0, 20)
    .map(({ __score, ...anime }) => anime);

  return { animes };
}

function extractEpisodeNumber(ep) {
  if (!ep) return null;

  const fields = [
    ep.episodeNumber,
    ep.ep,
    ep.sort,
    ep.number,
    ep.episode,
    ep.title,
    ep.episodeTitle,
  ];

  for (let i = 0; i < fields.length; i++) {
    const val = fields[i];
    if (val === undefined || val === null) continue;
    const m = String(val).match(/\d+/);
    if (m) return Number(m[0]);
  }

  return null;
}

async function getDetailById(params) {
  const { server, animeId, episode } = params;

  const response = await Widget.http.get(
    `${server}/api/v2/bangumi/${animeId}`,
    {
      headers: {
        "Content-Type": "application/json",
        "User-Agent": "ForwardWidgets/1.1.0",
      },
    }
  );

  const data = parseData(response);
  let episodes = data && data.bangumi && Array.isArray(data.bangumi.episodes)
    ? data.bangumi.episodes
    : [];

  const targetEpisode = episode !== undefined && episode !== null && episode !== ""
    ? Number(episode)
    : null;

  episodes.sort((a, b) => {
    const aNum = extractEpisodeNumber(a);
    const bNum = extractEpisodeNumber(b);

    if (targetEpisode !== null) {
      if (aNum === targetEpisode && bNum !== targetEpisode) return -1;
      if (bNum === targetEpisode && aNum !== targetEpisode) return 1;
    }

    if (aNum !== null && bNum !== null) return aNum - bNum;
    if (aNum !== null) return -1;
    if (bNum !== null) return 1;
    return 0;
  });

  return episodes;
}

async function getCommentsById(params) {
  const { server, commentId } = params;

  if (!commentId) return null;

  const response = await Widget.http.get(
    `${server}/api/v2/comment/${commentId}?withRelated=true&chConvert=1`,
    {
      headers: {
        "Content-Type": "application/json",
        "User-Agent": "ForwardWidgets/1.1.0",
      },
    }
  );

  return parseData(response);
}