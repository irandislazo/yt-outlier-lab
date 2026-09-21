# core/topics.py
"""
Clustering de temas con TF-IDF + KMeans.
"""
import json
import logging
import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize
from sqlalchemy import select

from core.models import Video, TopicCluster

logger = logging.getLogger(__name__)

STOPWORDS = {
    # Español
    "a","al","algo","ante","antes","como","con","cual","de","del","desde",
    "donde","durante","el","ella","en","entre","es","eso","esta","este",
    "hay","la","las","le","lo","los","mas","me","mi","muy","ni","no","nos",
    "o","para","pero","por","que","se","si","sin","sobre","son","su","sus",
    "te","ti","todo","un","una","uno","y","ya","yo","han","has","fue",
    # Inglés
    "a","about","after","all","am","an","and","are","as","at","be","been",
    "but","by","do","does","for","from","get","has","have","he","her","him",
    "his","how","i","if","in","into","is","it","its","me","my","no","not",
    "of","on","or","our","out","so","than","that","the","their","them",
    "then","there","they","this","to","up","us","was","we","were","what",
    "when","which","who","will","with","you","your",
    # YouTube noise
    "video","videos","shorts","youtube","canal","channel","ver","watch",
    "nuevo","new","mejores","best","completo","full","oficial","official",
    "2023","2024","2025","2026","parte","part","ep","episodio",
}


class TopicsEngine:

    def run(self, session, n_clusters: int = 12) -> int:
        videos = (
            session.execute(
                select(Video)
                .where(Video.title.isnot(None))
                .where(Video.view_count > 0)
            ).scalars().all()
        )

        if len(videos) < 15:
            logger.warning("Pocos videos para clusterizar.")
            return 0

        titles = [self._clean(v.title) for v in videos]

        try:
            vec = TfidfVectorizer(
                max_features=800,
                stop_words=list(STOPWORDS),
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.9,
            )
            matrix = vec.fit_transform(titles)
        except ValueError as e:
            logger.error(f"TF-IDF error: {e}")
            return 0

        matrix_norm = normalize(matrix, norm="l2")
        k = min(n_clusters, len(videos) // 3, 20)

        km = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=200)
        labels = km.fit_predict(matrix_norm)

        features = vec.get_feature_names_out()
        kw_map   = self._top_keywords(km, features)

        # Limpiar clusters anteriores
        session.query(TopicCluster).delete()
        session.flush()

        for cid in range(k):
            cvids = [v for v, lb in zip(videos, labels) if lb == cid]
            if not cvids:
                continue

            kws   = kw_map.get(cid, [])
            label = " + ".join(kws[:3]) or f"Cluster {cid}"

            scores    = [v.outlier_score for v in cvids]
            vels      = [v.views_per_hour for v in cvids if (v.views_per_hour or 0) > 0]
            out_count = sum(1 for s in scores if s >= 1.0)
            out_rate  = out_count / len(cvids)
            demand    = float(np.median(vels)) if vels else 0.0
            sat       = float(len(set(v.channel_id for v in cvids)))
            opp       = (demand * out_rate * 100 / sat) if sat > 0 else 0.0

            tc = TopicCluster(
                label             = label,
                keywords          = json.dumps(kws),
                video_count       = len(cvids),
                avg_outlier_score = float(np.mean(scores)),
                outlier_count     = out_count,
                demand_score      = round(demand, 2),
                saturation_score  = round(sat, 2),
                opportunity_score = round(opp, 4),
            )
            session.add(tc)
            session.flush()

            for v in cvids:
                v.topic_cluster = tc.id

        session.commit()
        return k

    def _clean(self, title: str) -> str:
        title = re.sub(r"http\S+", " ", title)
        title = re.sub(r"[^\w\s\u00C0-\u017E]", " ", title, flags=re.UNICODE)
        title = re.sub(r"\b\d{1,4}\b", " ", title)
        return re.sub(r"\s+", " ", title).lower().strip()

    def _top_keywords(self, km: KMeans, features, n: int = 8) -> dict:
        result = {}
        for i, center in enumerate(km.cluster_centers_):
            top = center.argsort()[::-1][:n]
            result[i] = [features[j] for j in top]
        return result