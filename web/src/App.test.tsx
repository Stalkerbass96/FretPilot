import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("FretPilot studio", () => {
  it("accepts a MIDI file and enables generation", async () => {
    const user = userEvent.setup();
    render(<App />);
    const file = new File(["midi"], "riff.mid", { type: "audio/midi" });

    expect(screen.getByRole("slider", { name: "MIDI 保真度" })).toBeInTheDocument();

    await user.upload(screen.getByLabelText("选择 MIDI 文件"), file);

    expect(screen.getByText("riff.mid")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /开始生成/ })).toBeEnabled();
  });

  it("rejects a non-MIDI file", () => {
    render(<App />);
    const file = new File(["text"], "notes.txt", { type: "text/plain" });

    fireEvent.change(screen.getByLabelText("选择 MIDI 文件"), {
      target: { files: [file] },
    });

    expect(screen.getByRole("alert")).toHaveTextContent("请选择 .mid 或 .midi 文件");
  });

  it("exposes the design system from primary navigation", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: "设计系统" }));

    expect(screen.getByRole("heading", { name: "克制、清晰、为音乐留白。" })).toBeInTheDocument();
    expect(screen.getByText("Quiet Studio · 0.1")).toBeInTheDocument();
  });
});
