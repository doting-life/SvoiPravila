import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { toErrorStatus } from "../../api/errors";
import type { RelationshipView } from "../../api/types";
import { useAppLanguage, useT } from "../../app/AppProviders";
import { ConfirmDialog, EmptyState, ErrorState, LoadingState } from "../../components/common";
import { Button, Card, Checkbox, Input, ListCell, ListSection, Notice, Row, Stack } from "../../components/ui";
import {
  useBootstrapQuery,
  useCreateRelationshipMutation,
  useDeleteRelationshipMutation,
  useSetDefaultRelationshipMutation,
} from "../../state/queries";
import { useUiStore } from "../../state/uiStore";
import { RELATION_TYPE_MAX_LENGTH, parseAliases, relationshipLabel } from "./format";

function CreateRelationshipForm({ onError }: { onError: (err: unknown) => void }) {
  const dict = useT();
  const createRelationship = useCreateRelationshipMutation();
  const [relationType, setRelationType] = useState("");
  const [aliases, setAliases] = useState("");
  const [setAsDefault, setSetAsDefault] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    try {
      await createRelationship.mutateAsync({
        relation_type: relationType.trim() || null,
        aliases: parseAliases(aliases),
        communication_style: {},
        set_as_default: setAsDefault,
      });
      setRelationType("");
      setAliases("");
      setSetAsDefault(false);
    } catch (err) {
      onError(err);
    }
  }

  return (
    <form onSubmit={onSubmit} noValidate>
      <Card header={dict.create}>
        <Input
          label={dict.relationType}
          value={relationType}
          maxLength={RELATION_TYPE_MAX_LENGTH}
          onChange={(event) => setRelationType(event.target.value)}
        />
        <Input label={dict.aliases} value={aliases} onChange={(event) => setAliases(event.target.value)} />
        <Checkbox label={dict.setAsDefault} checked={setAsDefault} onChange={setSetAsDefault} />
        <Stack>
          <Button type="submit" disabled={createRelationship.isPending} loading={createRelationship.isPending}>
            {dict.create}
          </Button>
        </Stack>
      </Card>
    </form>
  );
}

export function RelationshipsScreen() {
  const dict = useT();
  const { language } = useAppLanguage();
  const navigate = useNavigate();
  const bootstrap = useBootstrapQuery();
  const deleteRelationship = useDeleteRelationshipMutation();
  const setDefault = useSetDefaultRelationshipMutation();
  const selectedForRequest = useUiStore((state) => state.selectedRelationshipForRequest);
  const setRelationshipForRequest = useUiStore((state) => state.setRelationshipForRequest);
  const [pendingDelete, setPendingDelete] = useState<RelationshipView | null>(null);
  const [actionError, setActionError] = useState<unknown>(null);

  if (bootstrap.isPending) {
    return <LoadingState language={language} />;
  }
  if (bootstrap.isError) {
    return (
      <ErrorState
        language={language}
        status={toErrorStatus(bootstrap.error)}
        onRetry={() => {
          void bootstrap.refetch();
        }}
      />
    );
  }

  const { user, relationships } = bootstrap.data;
  const defaultId = user.default_relationship_id;

  async function confirmDelete() {
    const target = pendingDelete;
    setPendingDelete(null);
    if (!target) {
      return;
    }
    setActionError(null);
    try {
      await deleteRelationship.mutateAsync(target.relationship_id);
      if (selectedForRequest === target.relationship_id) {
        setRelationshipForRequest(null);
      }
    } catch (err) {
      setActionError(err);
    }
  }

  async function makeDefault(relationshipId: string) {
    setActionError(null);
    try {
      await setDefault.mutateAsync(relationshipId);
    } catch (err) {
      setActionError(err);
    }
  }

  return (
    <Stack>
      <h1>{dict.relationships}</h1>
      {actionError ? <ErrorState language={language} status={toErrorStatus(actionError)} /> : null}
      {relationships.length > 0 && defaultId === null ? <Notice>{dict.noDefaultRelationship}</Notice> : null}
      {relationships.length === 0 ? (
        <EmptyState message={dict.noRelationships} />
      ) : (
        <ListSection header={dict.relationships}>
          {relationships.map((relationship) => {
            const label = relationshipLabel(relationship, dict);
            const isDefault = relationship.relationship_id === defaultId;
            return (
              <div key={relationship.relationship_id} data-testid={`relationship-${relationship.relationship_id}`}>
                <ListCell subtitle={isDefault ? dict.defaultBadge : undefined}>{label}</ListCell>
                <Stack>
                  <Row>
                    <Button
                      mode="bezeled"
                      aria-label={`${dict.open}: ${label}`}
                      onClick={() => navigate(`/relationships/${encodeURIComponent(relationship.relationship_id)}`)}
                    >
                      {dict.open}
                    </Button>
                    {isDefault ? null : (
                      <Button
                        mode="bezeled"
                        aria-label={`${dict.makeDefault}: ${label}`}
                        disabled={setDefault.isPending}
                        onClick={() => {
                          void makeDefault(relationship.relationship_id);
                        }}
                      >
                        {dict.makeDefault}
                      </Button>
                    )}
                    <Button
                      mode="plain"
                      aria-label={`${dict.delete}: ${label}`}
                      disabled={deleteRelationship.isPending}
                      onClick={() => setPendingDelete(relationship)}
                    >
                      {dict.delete}
                    </Button>
                  </Row>
                </Stack>
              </div>
            );
          })}
        </ListSection>
      )}
      <CreateRelationshipForm onError={setActionError} />
      {pendingDelete ? (
        <ConfirmDialog
          language={language}
          message={dict.deleteRelationshipConfirm}
          onConfirm={() => {
            void confirmDelete();
          }}
          onCancel={() => setPendingDelete(null)}
        />
      ) : null}
    </Stack>
  );
}
