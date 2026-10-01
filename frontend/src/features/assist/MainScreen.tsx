import { type FormEvent, useState } from "react";

import { toErrorStatus } from "../../api/errors";
import type { MiniAppAssistBody, WorkflowName } from "../../api/types";
import { useAppLanguage, useT } from "../../app/AppProviders";
import { ErrorState, LoadingState } from "../../components/common";
import { Button, Card, Notice, Row, Select, Stack, TextArea } from "../../components/ui";
import { useAssistMutation, useBootstrapQuery } from "../../state/queries";
import { useUiStore } from "../../state/uiStore";
import { relationshipLabel } from "../relationships/format";
import { ResultView } from "./ResultView";

export const MAX_ASSIST_TEXT_LENGTH = 10_000;

const NO_OVERRIDE = "";

export function MainScreen() {
  const dict = useT();
  const { language } = useAppLanguage();
  const bootstrap = useBootstrapQuery();
  const assist = useAssistMutation();
  const workflow = useUiStore((state) => state.selectedWorkflow);
  const setWorkflow = useUiStore((state) => state.setWorkflow);
  const text = useUiStore((state) => state.draftText);
  const setText = useUiStore((state) => state.setDraftText);
  const override = useUiStore((state) => state.selectedRelationshipForRequest);
  const setOverride = useUiStore((state) => state.setRelationshipForRequest);
  const [validationError, setValidationError] = useState<string | null>(null);

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
  const defaultRelationship = relationships.find((item) => item.relationship_id === user.default_relationship_id) ?? null;
  const overrideRelationship =
    override !== null && override !== defaultRelationship?.relationship_id
      ? (relationships.find((item) => item.relationship_id === override) ?? null)
      : null;
  const selectableRelationships = relationships.filter(
    (item) => item.relationship_id !== defaultRelationship?.relationship_id,
  );

  const workflows: { name: WorkflowName; label: string }[] = [
    { name: "soften", label: dict.soften },
    { name: "decode", label: dict.decode },
    { name: "help-say", label: dict.helpSay },
  ];

  function selectWorkflow(next: WorkflowName) {
    setWorkflow(next);
    assist.reset();
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (text.trim().length === 0) {
      setValidationError(dict.validationEmpty);
      return;
    }
    if (text.length > MAX_ASSIST_TEXT_LENGTH) {
      setValidationError(dict.validationTooLong);
      return;
    }
    setValidationError(null);
    const body: MiniAppAssistBody = { text, language };
    if (overrideRelationship) {
      body.relationship_id = overrideRelationship.relationship_id;
    }
    assist.mutate({ workflow, body });
  }

  return (
    <form onSubmit={onSubmit} noValidate>
      <Stack>
        <h1>{dict.appTitle}</h1>
        <Row>
          {workflows.map((item) => (
            <Button
              key={item.name}
              mode={item.name === workflow ? "filled" : "bezeled"}
              aria-pressed={item.name === workflow}
              onClick={() => selectWorkflow(item.name)}
            >
              {item.label}
            </Button>
          ))}
        </Row>
        <Card header={dict.relationshipContext}>
          <Select
            label={dict.chooseRelationshipForRequest}
            value={overrideRelationship?.relationship_id ?? NO_OVERRIDE}
            onChange={(event) => setOverride(event.target.value === NO_OVERRIDE ? null : event.target.value)}
          >
            <option value={NO_OVERRIDE}>
              {defaultRelationship
                ? `${dict.useDefaultOption}: ${relationshipLabel(defaultRelationship, dict)}`
                : dict.noRelationshipOption}
            </option>
            {selectableRelationships.map((item) => (
              <option key={item.relationship_id} value={item.relationship_id}>
                {relationshipLabel(item, dict)}
              </option>
            ))}
          </Select>
          <Stack>
            {defaultRelationship && !overrideRelationship ? (
              <Notice>{`${dict.usingDefaultRelationship}: ${relationshipLabel(defaultRelationship, dict)}`}</Notice>
            ) : null}
            {!defaultRelationship ? <Notice>{dict.noDefaultRelationship}</Notice> : null}
            {!defaultRelationship && !overrideRelationship ? <Notice>{dict.noRelationshipContext}</Notice> : null}
          </Stack>
        </Card>
        <TextArea
          label={dict.inputPlaceholder}
          placeholder={dict.inputPlaceholder}
          value={text}
          error={validationError}
          onChange={(event) => setText(event.target.value)}
        />
        {validationError ? <Notice tone="error">{validationError}</Notice> : null}
        <Button type="submit" stretched disabled={assist.isPending} loading={assist.isPending}>
          {dict.submit}
        </Button>
        {assist.isPending ? <LoadingState language={language} /> : null}
        {assist.isError ? <ErrorState language={language} status={toErrorStatus(assist.error)} /> : null}
        {assist.isSuccess ? <ResultView key={assist.data.request_id} response={assist.data} dict={dict} /> : null}
      </Stack>
    </form>
  );
}
