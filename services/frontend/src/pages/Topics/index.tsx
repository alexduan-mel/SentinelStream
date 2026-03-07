import { useCallback } from "react";

import Card from "../../components/Card";
import Chip from "../../components/Chip";
import ProgressBar from "../../components/ProgressBar";
import { listTopics } from "../../api/topicsApi";
import { useAsyncData } from "../../hooks/useAsyncData";

export default function TopicsPage() {
  const loadTopics = useCallback(() => listTopics(), []);
  const { data } = useAsyncData(loadTopics);
  const topics = data ?? [];

  return (
    <div className="flex flex-col gap-24">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-text-primary">Topics</h1>
        <p className="text-sm text-text-secondary font-normal">Market pulse and discovery pipeline</p>
      </div>
      <div className="grid grid-cols-3 gap-24">
        {topics.map((topic) => (
          <Card key={topic.id} variant="compact">
            <div className="flex items-start justify-between">
              <div className="flex flex-col gap-8">
                <div className="text-body text-text-primary">{topic.name}</div>
                <div className="flex flex-wrap gap-8">
                  {topic.tags.map((tag) => (
                    <Chip key={tag} tone="neutral">
                      {tag}
                    </Chip>
                  ))}
                </div>
                <Chip tone="info">{topic.status}</Chip>
              </div>
              <div className="text-label text-semantic-warning">{topic.score.toFixed(1)}</div>
            </div>
            <div className="mt-16 flex items-center justify-between">
              <div className="text-caption text-text-muted">Upgrade eligible</div>
              <div className="w-64">
                <ProgressBar value={topic.progress} tone="positive" />
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
