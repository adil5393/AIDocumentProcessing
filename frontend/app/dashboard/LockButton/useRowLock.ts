import { useState } from "react";

export function useRowLock<T extends string | number>() {
  const [unlockedRows, setUnlockedRows] = useState<Record<T, boolean>>({} as Record<T, boolean>);

  function isRowEditable(id: T) {
    return !!unlockedRows[id];
  }

  function unlockRow(id: T) {
    setUnlockedRows(prev => ({ ...prev, [id]: true }));
  }

  function lockRow(id: T) {
    setUnlockedRows(prev => {
      const copy = { ...prev };
      delete copy[id];
      return copy;
    });
  }

  function setRow(id: T, value: boolean) {
    setUnlockedRows(prev => ({ ...prev, [id]: value }));
  }

  return {
    isRowEditable,
    unlockRow,
    lockRow,
    setRow
  };
}
