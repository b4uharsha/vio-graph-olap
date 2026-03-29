#!/usr/bin/env bash
# Local dev helper: watches for pending snapshots with placeholder SQL
# and marks them as ready (data must be pre-uploaded to GCS).
# Usage: ./local-snapshot-helper.sh

set -euo pipefail
NAMESPACE="graph-olap-local"
PG_POD="postgres-7b877fc959-lnf4m"
GCS_SVC="http://fake-gcs-local:4443"
BUCKET="graph-olap-local-dev"
DATA_DIR="${1:-/tmp/ipl-graph}"

echo "Local snapshot helper running... (Ctrl+C to stop)"
echo "Data source: $DATA_DIR"

while true; do
  # Find pending snapshots
  PENDING=$(kubectl exec -n $NAMESPACE $PG_POD -- psql -U control_plane -d control_plane -t -A -c "
    SELECT s.id, s.gcs_path FROM snapshots s
    WHERE s.status = 'pending'
    AND NOT EXISTS (SELECT 1 FROM export_jobs ej WHERE ej.snapshot_id = s.id)
  " 2>/dev/null || true)
  
  for row in $PENDING; do
    SID=$(echo "$row" | cut -d'|' -f1)
    GCS_PATH=$(echo "$row" | cut -d'|' -f2)
    
    if [ -z "$SID" ]; then continue; fi
    
    echo "Found pending snapshot $SID at $GCS_PATH"
    
    # Extract prefix from gs://bucket/prefix/
    PREFIX=$(echo "$GCS_PATH" | sed "s|gs://$BUCKET/||" | sed 's|/$||')
    
    # Upload parquet files via fake-GCS
    GCS_POD=$(kubectl get pods -n $NAMESPACE -l app=fake-gcs-local -o jsonpath='{.items[0].metadata.name}')
    
    for TYPE in nodes/Team nodes/Player nodes/Game edges/PLAYS_FOR edges/PLAYED_IN edges/WON; do
      LOCAL="$DATA_DIR/$TYPE/data.parquet"
      if [ -f "$LOCAL" ]; then
        REMOTE="$PREFIX/$TYPE/data.parquet"
        # Upload via port-forward or kubectl exec
        kubectl cp "$LOCAL" "$NAMESPACE/$GCS_POD:/tmp/upload.parquet" 2>/dev/null
        kubectl exec -n $NAMESPACE $GCS_POD -- wget -q -O/dev/null --post-file=/tmp/upload.parquet \
          "$GCS_SVC/upload/storage/v1/b/$BUCKET/o?uploadType=media&name=$REMOTE" 2>/dev/null && \
          echo "  Uploaded $TYPE" || echo "  Failed $TYPE"
      fi
    done
    
    # Mark snapshot as ready
    kubectl exec -n $NAMESPACE $PG_POD -- psql -U control_plane -d control_plane -c \
      "UPDATE snapshots SET status = 'ready' WHERE id = $SID;" 2>/dev/null
    echo "Snapshot $SID marked as ready"
  done
  
  sleep 5
done
